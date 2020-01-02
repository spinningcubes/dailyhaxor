import datetime
import time
import subprocess

class DailyHaxor:
	'DailyHaxor generates github style activity boxes in html from selected local repository'

	# Settings
	saveFile = ""				# Where the final html will be saved
	daysBack = 7				# How many days back to scan each repository

	# Works variables
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

	def scanRepository(self, reptype, repname, repository, username):
		now = datetime.date.today()

		for i in range(1,self.daysBack):
			daystr = str(now)

			if reptype=="hg":
				commitByDay = self.GetCommitsOnDay_hg(repository, now, username)
			else:
				commitByDay = self.GetCommitsOnDay_Git(repository, now, username)

			if commitByDay > 0:
				if daystr in self.dailyCommits:
					self.dailyCommits[daystr] = self.dailyCommits[daystr] + commitByDay
				else:
					self.dailyCommits[daystr] = commitByDay

				self.maxActivity = max(self.maxActivity, self.dailyCommits[daystr])

				if daystr in self.dailyTitles:
					self.dailyTitles[daystr] = self.dailyTitles[daystr] + ", " + repname + " " + str(commitByDay)
				else:
					self.dailyTitles[daystr] = repname + " " + str(commitByDay)

			now -= datetime.timedelta(days=1)
