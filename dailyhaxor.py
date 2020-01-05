import datetime
import time
import subprocess
import os

class Repository:
	def  __init__(self, name):
		self.name = name
		self.dailyCommits = {}	# Number of commits on a day.

	def ClearCommits(self,day):
		if day in self.dailyCommits:
			del self.dailyCommits[day]

	def GetCommits(self,day):
		if day in self.dailyCommits:
			return self.dailyCommits[day]

		return 0

	def SetCommits(self,day, commits):
		self.dailyCommits[day] = commits

	def DataExists(self,day):
		if day in self.dailyCommits:
			return True
		
		return False

class DailyHaxor:
	'DailyHaxor generates github style activity boxes in html from selected local repository'

	# Settings
	saveFile = ""				# Where the final html will be saved
	daysBack = 7				# How many days back to scan each repository

	# Works variables
	repositories = dict()
	currentRepository = None

	dailyCommits = {}			# Number of commits on a day.
	dailyTitles = {}			# Text for a day.
	maxActivity = 0				# Max number of commits find in a single day.

	# Colors for activity
	commitColors = {}			# Colors for commit activity. Will be scaled to the maxActivity range. 
	commitColors[0] = "eeeeee"
	commitColors[1] = "d6e685"
	commitColors[2] = "8cc665"
	commitColors[3] = "44a340"
	commitColors[4] = "1e6823"

	def  __init__(self, targetFile, daysToScan):
		self.saveFile = targetFile
		self.daysBack = daysToScan

	def WriteHtmlHeader(self, f):
		 f.write('<HTML>\n')
		 f.write('<BODY>\n')

	def WriteHtmlFooter(self, f):
		 f.write('</BODY>\n')
		 f.write('</HTML>\n')

	def GetColor(self, commits):
		color = self.commitColors[0]
		if commits == 0:
			return color

		if self.maxActivity > 4:
			commitRange = self.maxActivity / 4
		else:
			commitRange = 1

		if commits <= commitRange:
			return self.commitColors[1]
		elif commits <= commitRange * 2:
			return self.commitColors[2]
		elif commits <= commitRange * 3:
			return self.commitColors[3]
		elif commits <= commitRange * 4:
			return self.commitColors[4]

		return self.commitColors[4]

	def WriteHtml(self ):
		self.MergeData()

		daily_y = 0
		daily_x = 0

		now = datetime.date.today()
		now -= datetime.timedelta(days=self.daysBack)
		daily_y = now.weekday() * 13

		f = open(self.saveFile, 'w')
		self.WriteHtmlHeader(f)

		f.write('<center>\n')
		f.write('<svg width="721" height="110">\n')
		f.write('   <g transform="translate(0, 0)">\n')

		for i in range(self.daysBack,-1,-1):
			now = datetime.date.today()
			now -= datetime.timedelta(days=i)
			daystr = str(now)

			data_points = 0
			if str(now) in self.dailyCommits:
				data_points = self.dailyCommits[str(now)]

			color = self.GetColor(data_points)

			f.write('      <rect class="day" width="11" height="11" y="' + str(daily_y))
			f.write('" fill="#' + color + '">\n')

			if daystr in self.dailyTitles:
				f.write('         <title>' + daystr + ' ' + self.dailyTitles[daystr] + '</title>\n')
			else:
				f.write('         <title>' + daystr + '</title>\n')

			f.write('      </rect>\n')

			daily_y += 13

			if daily_y >= 79:
				daily_y = 0
				daily_x += 13
				f.write('   </g>\n')
				f.write('   <g transform="translate(' + str(daily_x) + ', 0)">\n')
		
		f.write('   </g>\n')
		f.write('</svg>\n')
		f.write('</center>\n')

		self.WriteHtmlFooter(f)
		f.close()

	def GetCommitsOnDay_hg(self, path, theDate, theUser):
		strDate = str(theDate)
		args = ["hg", "log", "-d", strDate, "--template" ,  "*"]
		
		if theUser != None:
			args.append("-u")
			args.append(theUser)

		pipe = subprocess.Popen(
	        args,
	        stdout=subprocess.PIPE,
	        cwd=path)
	    
		result = pipe.stdout.read()
		result_str = result.decode()
		return str.count(result_str, "*" )

	def GetCommitsOnDay_Git(self, path, theDate, theUser ):
		strDate = str(theDate)
		args = ["git", "log", '--pretty=format:*']

		if theUser != None:
			args.append("--author=" + theUser )
		
		args.append('--after="' + strDate + ' 00:00"')
		args.append('--before="' + strDate + ' 23:59"')
		pipe = subprocess.Popen(
	        args,
	        stdout=subprocess.PIPE,
	        cwd=path)
	    
		result = pipe.stdout.read()
		result_str = result.decode()
		return str.count(result_str, "*" )

	def GetCommitsOnDay_perforce(self, path, theDate, theUser ):
		startDateStr = str(theDate)
		endDateStr = str(theDate + datetime.timedelta(days=1))

		startDateStr = startDateStr.replace("-", "/")
		endDateStr = endDateStr.replace("-", "/")

		args = ["p4", "changes", '-s' , 'submitted',  '-u', 'vim']
		args.append('@' + startDateStr + ':00:00:00,' + endDateStr + ':00:00:00')

		pipe = subprocess.Popen(
	        args,
	        stdout=subprocess.PIPE,
	        cwd=path)
	    
		result = pipe.stdout.read()
		result_str = result.decode()
		return str.count(result_str, "Change" )

	def GetCommitsOnDay_svn(self, path, theDate, theUser ):
		return 0

	def GetCommitsOnDay(self, reptype, path, theDate, theUser ):
		commitByDay = 0

		daystr = str(theDate)

		if self.currentRepository.DataExists(daystr):
			return self.currentRepository.GetCommits(daystr)

		print("   ", daystr )

		if reptype=="hg":
			commitByDay = self.GetCommitsOnDay_hg(path, theDate, theUser)
		elif  reptype=="git":
			commitByDay = self.GetCommitsOnDay_Git(path, theDate, theUser)
		elif  reptype=="perforce":
			commitByDay = self.GetCommitsOnDay_perforce(path, theDate, theUser)

		return commitByDay

	def LoadDB(self, repname):
		if repname not in self.repositories:
			self.repositories[repname] = Repository(repname)

		repository = self.repositories[repname]

		fileName = "db_" + repname + ".txt"
		if not os.path.exists(fileName):
			return 

		f = open(fileName, 'r')

		lines = f.readlines()
		f.close()

		for l in lines:
			words = l.split('=')
			repository.dailyCommits[words[0]] = int(words[1])

	def SaveDB(self, repname):
		repository = self.repositories[repname]

		fileName = "db_" + repname + ".txt"

		f = open(fileName, 'w')

		now = datetime.date.today()
		for i in range(1,self.daysBack):
			daystr = str(now)
			txt = daystr + "=" + str(repository.dailyCommits[daystr]) + "\n"
			f.write(txt)
			now -= datetime.timedelta(days=1)

		f.close()

	def MergeData(self):
		# Clean target data
		self.dailyCommits = {}		
		self.dailyTitles = {}			
		self.maxActivity = 0			

		now = datetime.date.today()

		for i in range(1,self.daysBack):
			daystr = str(now)
			totalCommits = 0

			for key in self.repositories:
				repository = self.repositories[key]
				repCommits = repository.GetCommits(daystr)

				if repCommits > 0:
					totalCommits = totalCommits + repCommits

					if daystr in self.dailyTitles:
						self.dailyTitles[daystr] = self.dailyTitles[daystr] + ", " + repository.name + " " + str(repCommits)
					else:
						self.dailyTitles[daystr] = repository.name + " " + str(repCommits)
			
			if totalCommits > 0:
				self.dailyCommits[daystr] = totalCommits
				self.maxActivity = max(self.maxActivity, totalCommits)

			now -= datetime.timedelta(days=1)


	def scanRepository(self, reptype, repname, repository, username):
		self.LoadDB(repname)
		self.currentRepository = self.repositories[repname]

		if repository == None:
			return					# Do not update existing database

		now = datetime.date.today()

		print("Update repository ", repname )
		self.currentRepository.ClearCommits(str(now))	# Clear todays commits to get it again

		for i in range(1,self.daysBack):
			daystr = str(now)

			commitByDay = self.GetCommitsOnDay(reptype, repository, now, username)
			self.currentRepository.SetCommits(daystr, commitByDay)
			now -= datetime.timedelta(days=1)

		self.SaveDB(repname)
