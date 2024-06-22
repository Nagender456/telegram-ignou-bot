import warnings
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import numpy as np
warnings.filterwarnings("ignore")

class MessageHandler:
	def __init__(self):
		self.botNames = ["ritu", "titu"]
		self.response = []
		self.possibleCommands = [
			"result", "marks", "grade", "grades", "gradecard", 
			"astatus", 
			"status",
			"name",
			"centre",
			"enrolment", "enrol",
			"date", "datesheet",
			"sub", "subject",
			"saveme", "me",
			"commands", "command", "help",
			"percent", "percentage", "%",
			"rank", "ranks", "leaderboard",
			"updateranks",
			"publicranks",
			"graph",
		]
		#"updatepublic"
		
		self.subjects_data = {
			'50': ['FEG02', 'ECO01', 'BCSL013', 'ECO02', 'MCS013', 'MCS015', 'BCSL021', 'BCSL022', 'BCSL032', 'BCSL033', 'BCSL034', 'BCS040', 'BCS042', 'MCSL016', 'BCSL043', 'BCSL043', 'BCSL044', 'BCSL045', 'BCS053', 'BCS055', 'BCSL056', 'BCSL057', 'BCSL058', 'BCS062', 'BCSL063'],
			'ASS_30': ['FEG02', 'ECO01', 'ECO02'],
			'200': ['BCSP064']
		}

		self.passing_marks_35_subjects = ['FEG02', 'ECO01', 'ECO02', 'BCS040']

		self.semester_subjects = {
			1: ['FEG02', 'ECO01', 'BCS011', 'BCS012', 'BCSL013'],
			2: ["ECO02", "MCS011", "MCS012", "MCS015", "MCS013", "BCSL021", "BCSL022"],
			3: ["MCS021", "MCS023", "MCS014", "BCS031", "BCSL032", "BCSL033", "BCSL034"],
			4: ["BCS040", "MCS024", "BCS041", "BCS042", "MCSL016", "BCSL043", "BCSL044", "BCSL045"],
			5: ["BCS051", "BCS052", "BCS053", "BCS054", "BCS055", "BCSL056", "BCSL057", "BCSL058"],
			6: ["BCS062", "MCS022", "BCSL063", "BCSP064"]
		}

	async def handleMessage(self, event, teleBot):
		self.message = event.message.message.lower()
		self.event = event
		# Check if mentioned, return if not
		mentioned = await self.isMentioned()
		reply_mentioned = event.mentioned
		if not (mentioned or reply_mentioned): 
			return []
		
		chat = await event.get_chat()
		if chat.id not in [1777153000]:
			await teleBot.forward_messages(-1001842525756, event.message)

		# Parse Message
		messageParts = self.message.split()

		# Check the command
		command, dataParts = self.getCommand(messageParts)

		# Return if command didn"t match
		if command is None:
			if mentioned:
				return [(1, None, "Use `ritu help` for help!")]
			return []

		self.response = []

		# Perform action based on command
		if command in ["marks", "result", "grade", "gradecard", "grades"]:
			requiredResponse = await self.getMarksResponse(dataParts)
			if requiredResponse[-1] is None:
				requiredResponse = await self.getResultResponse(dataParts)
			self.response.append(requiredResponse)

		elif command in ["status"]:
			requiredResponse = await self.getStatusResponse(dataParts)
			self.response.append(requiredResponse)
		
		elif command in ["name"]:
			requiredResponse = await self.getNameResponse(dataParts)
			self.response.append(requiredResponse)
		
		elif command in ["enrolment", "enrol"]:
			requiredResponse = await self.getEnrolmentResponse(dataParts)
			self.response.append(requiredResponse)
		
		elif command in ["datesheet", "date"]:
			requiredResponse = self.getDateSheetResponse(dataParts)
			self.response.append(requiredResponse)
		
		elif command in ["sub", "subject"]:
			requiredResponse = self.getSubjectDetailResponse(dataParts)
			self.response.append(requiredResponse)
		
		elif command in ["saveme"]:
			requiredResponse = await self.setNameInTelegram(dataParts)
			self.response.append(requiredResponse)

		elif command in ["centre"]:
			requiredResponse = await self.getExamCenterResponse(dataParts)
			self.response.append(requiredResponse)
		
		elif command in ["command", "commands", "help"]:
			with open('./data/templates/commands.txt') as file:
				requiredResponse = file.read()
			return [(1, None, requiredResponse)]
		
		elif command in ["graph"]:
			requiredResponse = await self.getGraphResponse(dataParts)
			self.response.append(requiredResponse)

		elif command in ["me"]:
			requiredResponse = await self.getNameFromTelegramResponse()
			self.response.append(requiredResponse)

		elif command in ["astatus"]:
			requiredResponse = await self.getAstatusResponse(dataParts)
			self.response.append(requiredResponse)
		
		elif command in ["percent", "percentage", "%"]:
			requiredResponse = await self.getPercentageResponse(dataParts)
			self.response.append(requiredResponse)
		
		elif command in ["leaderboard", "ranks", "rank"]:
			requiredResponse = self.getPrivateLeaderBoardResponse()
			self.response.append(requiredResponse)
		
		elif command in ["publicranks"]:
			requiredResponse = self.getPublicLeaderBoardResponse()
			self.response.append(requiredResponse)
		
		elif command in ["updateranks"]:
			requiredResponse = await self.updatePrivateLeaderBoard()
			self.response.append(requiredResponse)
		
		elif command in ["updatepublic"]:
			requiredResponse = await self.updatePublicLeaderBoard()
			self.response.append(requiredResponse)

		# elif command in ["result"]:
		# 	resultResponse = await self.getResultResponse(dataParts)
		# 	self.response.append(resultResponse)


		return self.response
	
	async def getStatusResponse(self, dataParts):
		studentName = []
		for dataPart in dataParts:
			studentName.append(dataPart)
		studentName = " ".join(studentName)
		enrolmentNumber = await self.getEnrolmentNumber(studentName)
		if enrolmentNumber is None:
			return (1, None, "Enrolment not found!")
		studentName, resultData, finalPercentage = await self.getResult(enrolmentNumber)

		statusData = {
			'backlogTermEnd': [],
			'backlogAssignments': [],
			'remainingTermEnd': [],
			'remainingAssignments': []
		}
		
		for sem in range(1, 7):
			for subject, subjectMarks in resultData[sem].items():
				if subject in self.passing_marks_35_subjects:
					if subjectMarks[0] <= 0:
						statusData['remainingAssignments'].append((sem, subject))
					elif subjectMarks[0] < 35:
						statusData['backlogAssignments'].append((sem, subject))
					if subjectMarks[1] <= 0:
						statusData['remainingTermEnd'].append((sem, subject))
					elif subjectMarks[1] < 35:
						statusData['backlogTermEnd'].append((sem, subject))
				else:
					if subjectMarks[0] <= 0:
						statusData['remainingAssignments'].append((sem, subject))
					elif subjectMarks[0] < 40:
						statusData['backlogAssignments'].append((sem, subject))
					if subjectMarks[1] <= 0:
						statusData['remainingTermEnd'].append((sem, subject))
					elif subjectMarks[1] < 40:
						statusData['backlogTermEnd'].append((sem, subject))
			for subject in self.semester_subjects[sem]:
				if subject not in resultData[sem]:
					statusData['remainingTermEnd'].append((sem, subject))
					if subject != 'BCSP064':
						statusData['remainingAssignments'].append((sem, subject))
		
		requiredResponse = self.formatStatusResponse(studentName, statusData, finalPercentage)
		return (1, None, requiredResponse)
	
	def formatStatusResponse(self, studentName, statusData, finalPercentage):
		teeBacklogs = statusData['backlogTermEnd']
		assBacklogs = statusData['backlogAssignments']
		teeRem = statusData['remainingTermEnd']
		assRem = statusData['remainingAssignments']

		requiredResponse = f"**{studentName}**\n\n"

		if len(teeBacklogs) + len(assBacklogs) + len(teeRem) + len(assRem) <= 0:
			requiredResponse += f"**Completed with {finalPercentage}%!**"

		if len(teeBacklogs) > 0:
			requiredResponse += f"**TEE Backlogs ({len(teeBacklogs)}):**\n"
			for sem, subject in teeBacklogs:
				requiredResponse += f"` {sem} - {subject}`\n"
			requiredResponse += '\n'
		
		if len(assBacklogs) > 0:
			requiredResponse += f"**ASS Backlogs ({len(assBacklogs)}):**\n"
			for sem, subject in assBacklogs:
				requiredResponse += f"` {sem} - {subject}`\n"
			requiredResponse += '\n'

		if len(teeRem) > 0:
			requiredResponse += f"**TEE Remaining ({len(teeRem)}):**\n"
			for sem, subject in teeRem:
				requiredResponse += f"` {sem} - {subject}`\n"
			requiredResponse += '\n'
		
		if len(assRem) > 0:
			requiredResponse += f"**ASS Remaining ({len(assRem)}):**\n"
			for sem, subject in assRem:
				requiredResponse += f"` {sem} - {subject}`\n"
			requiredResponse += '\n'
				
		return requiredResponse

	async def getPercentageResponse(self, dataParts):
		studentName = []
		for dataPart in dataParts:
			studentName.append(dataPart)
		studentName = " ".join(studentName)
		enrolmentNumber = await self.getEnrolmentNumber(studentName)
		if enrolmentNumber is None:
			return (1, None, "Enrolment not found!")
		percentage = await self.getPercentage(enrolmentNumber)
		if percentage is not None:
			percentageResponse = f"`{percentage}%`"
		else:
			percentageResponse = f"`Couldn't get percentage!\nPlease check input and try again!`"
		return (1, None, percentageResponse)
	
	async def getPercentage(self, enrolmentNumber, validation=False):
		try:
			resultResponse = await self.getResult(enrolmentNumber)
			if validation:
				totalTeeMarks = 0
				totalAssMarks = 0
				for subject in resultResponse[1:][:-1]:
					# subjectNameString = subject[0]
					assMarksString = subject[1]
					teeMarksString = subject[2] if subject[2] != '-' else subject[3]
					assMarks = int(assMarksString) if assMarksString != '-' else 0
					teeMarks = int(teeMarksString) if teeMarksString != '-' else 0
					totalTeeMarks += teeMarks
					totalAssMarks += assMarks
				if totalTeeMarks < 200:
					return None
			percentage = float(resultResponse[-1])
		except Exception as e:
			percentage = None
		return percentage 
	
	async def getAstatusResponse(self, dataParts):
		studentName = []
		for dataPart in dataParts:
			studentName.append(dataPart)
		studentName = " ".join(studentName)
		enrolmentNumber = await self.getEnrolmentNumber(studentName)
		if enrolmentNumber is None:
			return (1, None, "Enrolment not found!")
		astatusResponse = await self.getAstatus(enrolmentNumber)
		if astatusResponse is None:
			return (1, None, "Couldn't get Assignment Status!")
		astatusResponse = self.formatAstatusResponse(astatusResponse)
		return (1, None, astatusResponse)
	
	async def getAstatus(self, enrolmentNumber):
		# url = "https://admission.ignou.ac.in/changeadmdata/StatusAssignment.ASP"
		url = "https://isms.ignou.ac.in/changeadmdata/StatusAssignment.ASP"
		params = {'EnrNo':enrolmentNumber, 'program':'BCA', 'Submit':1}

		res = requests.post(url, params = params,verify=False)
		htmlParser = BeautifulSoup(res.text, 'html.parser')

		data = [x.get_text() for x in htmlParser.find_all("td")]

		def adjMsg(string):
			string = string.replace("Check Grade Card Status for detail.", "Marks Updated!")
			string = string.replace("Received and in-Process", "In-Process.")
			string = string.replace("Received to be Processed", "Yet to Process.")
			return string
		
		finalData = []
		for i in range(8, len(data), 5):
			finalData.append((data[i+1].strip().upper(), adjMsg(data[i+3].strip())))
			# req.append("`{}`".format(adjStr(data[i+1], 10) + adjMsg(data[i+3])))
		# return '\n'.join(req)
		return finalData
	
	def formatAstatusResponse(self, astatusResponse):
		semSubjects = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 'other': []}
		for subject, status in astatusResponse:
			found = False
			for key, val in self.semester_subjects.items():
				if subject in val or self.getAlternateSubjectCode(subject) in val:
					semSubjects[key].append((subject, status))
					found = True
					break
			if not found:
				semSubjects['other'].append((subject, status))
				# else:
				# 	semSubjects["other"].append((subject, status))
		
		formattedResponse = '`' + self.fillString("Subject", ' ', 10, 1) + "Status" + '`' + '\n'

		for sem in range(1, 7):
			if len(semSubjects[sem]) < 1: continue
			formattedResponse += '`      `' + '**' + f"Semester {sem}" + '**' + '\n'
			for subject, status in semSubjects[sem]:
				formattedResponse += '`' + self.fillString(subject, ' ', 10, 1) + status + '`' + '\n'

		if len(semSubjects["other"]) > 0:
			formattedResponse += '`        `' + '**' + "Other" + '**' + '\n'
			for subject, status in semSubjects["other"]:
				formattedResponse += '`' + self.fillString(subject, ' ', 10, 1) + status + '`' + '\n'
		return formattedResponse

	
	async def getGraphResponse(self, dataParts):
		import random
		studentName = []
		for dataPart in dataParts:
			studentName.append(dataPart)
		studentName = " ".join(studentName)
		enrolmentNumber = await self.getEnrolmentNumber(studentName)
		if enrolmentNumber is None:
			return (1, None, "Enrolment not found!")
		_, completeSemData, _ = await self.getResult(enrolmentNumber)
		fileName = str(random.randint(1, 10000)) + '.png'
		self.plot_semester_data(completeSemData, fileName)
		return (3, fileName, None)

	async def getExamCenterResponse(self, dataParts):
		studentName = []
		for dataPart in dataParts:
			studentName.append(dataPart)
		studentName = " ".join(studentName)
		enrolmentNumber = await self.getEnrolmentNumber(studentName)
		if enrolmentNumber is None:
			return (1, None, "Enrolment not found!")
		examCenterResponse = await self.getExamCenter(enrolmentNumber)
		if examCenterResponse is None:
			return (1, None, "Couldn't get exam center!")
		examCenterResponse = self.formatExamCenterResponse(examCenterResponse)
		return (1, None, examCenterResponse)

	async def getExamCenter(self, enrolmentNumber):
		# https://hall_ticket.ignou.ac.in/hall0624/ignouhallticketjun2024.aspx
		URL = f"https://hall_ticket.ignou.ac.in/hall0624/ignouhallticketjun2024.aspx?submit=1&enrno={enrolmentNumber}&program=BCA"
		# URL = f"https://admission.ignou.ac.in/changeadmdata/StatusExam.asp?submit=1&enrno={enrolmentNumber}&program=BCA"
		urlResponse = requests.post(URL, verify=False)
		htmlParser = BeautifulSoup(urlResponse.text, "html.parser")
		try:

			dataElements = htmlParser.find_all("tr", class_="td2")[-1].find_all('td')
			centerCode, centerName = dataElements[1].text.split(':')
			subjectsFilled = dataElements[2].text
			studentName = "Unknown"
			try:
				studentName = await self.getStudentName(enrolmentNumber)
			except:
				pass
			return studentName, centerCode, centerName, subjectsFilled
		except Exception as e:
			return None

	def formatExamCenterResponse(self, examCenterResponse):
		studentName, centerCode, centerName, subjectsFilled = examCenterResponse
		subjects = "\n".join([f"{i+1}.) {subject}" for i, subject in enumerate(subjectsFilled.split())])
		requiredResponse = f"**{studentName}**\n\nCentre chosen:\n`{centerName} ({centerCode})`\n\nSubjects:\n`{subjects}`"
		return requiredResponse
	
	async def setNameInTelegram(self, dataParts):
		try:
			senderName = ' '.join(dataParts)
			if len(senderName) < 3:
				return (1, None, "`Name is Invalid!`")
			sender = await self.event.get_sender()
			senderId = str(sender.id)
			savedUsersDict = dict()
			with open('saved-users.txt', 'r') as file:
				savedUsers = [x.strip() for x in file.readlines()]
				for user in savedUsers:
					teleId, teleName = user.split()[0], ' '.join(user.split()[1:])
					savedUsersDict[teleId] = teleName
			savedUsersDict[senderId] = senderName
			with open('saved-users.txt', 'w') as file:
				for userId, userName in savedUsersDict.items():
					line = userId + ' ' + userName + '\n'
					file.write(line)
			return (1, None, f"Successfully linked name **{senderName.capitalize()}** to your Telegram Id!")
		except Exception as e:
			return (1, None, "`Something went wrong!`")
		
	async def getNameFromTelegramResponse(self):
		requiredName = await self.getNameFromTelegram()
		if requiredName is None:
			return (1, None, f"You're not in my record!\n\nTry saving your name using following syntax:\n{self.botNames[0]} saveme `Your Name`")
		return (1, None, f"You're {requiredName.capitalize()}")
	
	async def getNameFromTelegram(self):
		sender = await self.event.get_sender()
		senderId = str(sender.id)
		savedUsersDict = dict()
		with open('saved-users.txt', 'r') as file:
			savedUsers = [x.strip() for x in file.readlines()]
			for user in savedUsers:
				teleId, teleName = user.split()[0], ' '.join(user.split()[1:])
				savedUsersDict[teleId] = teleName
		senderName = savedUsersDict.get(senderId, None)
		return senderName

	def getDateSheetResponse(self, dataParts):
		subjects = []
		for dataPart in dataParts:
			if ',' in dataPart:
				for subPart in dataPart.split(','):
					if self.isValidSubjectCode(subPart):
						subjects.append(subPart.replace('-', '').upper())
				continue
			if self.isValidSubjectCode(dataPart):
				subjects.append(dataPart.replace('-', '').upper())
		dateSheetResponse = self.getDateSheet(subjects)
		dateSheetResponse = self.formatDateSheetResponse(dateSheetResponse)
		return (1, None, dateSheetResponse)

	def getDateSheet(self, subjects):
		semDict = { 'SEM1' : [], 'SEM2' : [], 'SEM3' : [], 'SEM4' : [], 'SEM5' : [], 'SEM6' : [] }
		with open('./data/ignou/courseInfo.txt', 'r') as file:
			lines = file.readlines()
			curSem = 0
			for line in lines:
				if len(line) < 3:
					curSem += 1
					continue
				semDict[f"SEM{curSem}"].append(line.split()[0])
		for sub in subjects:
			if sub in semDict:
				for extraSub in semDict[sub]:
					subjects.append(extraSub)
		for i in range(len(subjects)):
			if subjects[i] not in semDict:
				subjects.append(self.getAlternateSubjectCode(subjects[i]))
		requiredData = []
		with open('./data/ignou/datesheetData.txt', 'r') as file:
			lines = file.readlines()
			for line in lines:
				if len(line) < 3: continue
				words = line.split()
				curDate = words[0]
				curDay = words[1]
				for courseCode in words[2:]:
					if courseCode in subjects:
						requiredData.append((curDate, curDay, courseCode))
		return requiredData

	def formatDateSheetResponse(self, dateSheetResponse):
		requiredResponse = ''
		for date, day, subject in dateSheetResponse:
			requiredResponse += f"{date} ({day}) - {subject}\n"
		requiredResponse += '\n(Tentative)'
		requiredResponse = '`' + requiredResponse + '`'
		return requiredResponse

	def getSubjectDetailResponse(self, dataParts):
		subjects = []
		for dataPart in dataParts:
			if ',' in dataPart:
				for subPart in dataPart.split(','):
					if self.isValidSubjectCode(subPart):
						subjects.append(subPart.replace('-', '').upper())
				continue
			if self.isValidSubjectCode(dataPart):
				subjects.append(dataPart.replace('-', '').upper())
		subjectDetailResponse = self.getSubjectDetail(subjects)
		subjectDetailResponse = self.formatSubjectDetailResponse(subjectDetailResponse)
		return (1, None, subjectDetailResponse)
	
	def getSubjectDetail(self, subjects):
		semDict = { 'SEM1' : [], 'SEM2' : [], 'SEM3' : [], 'SEM4' : [], 'SEM5' : [], 'SEM6' : [] }
		with open('./data/ignou/courseInfo.txt', 'r') as file:
			lines = file.readlines()
			curSem = 0
			for line in lines:
				if len(line) < 3:
					curSem += 1
					continue
				semDict[f"SEM{curSem}"].append(line.split()[0])
		for sub in subjects:
			if sub in semDict:
				for extraSub in semDict[sub]:
					subjects.append(extraSub)
		requiredResponse = []
		for i in range(len(subjects)):
			subjects.append(self.getAlternateSubjectCode(subjects[i]))
		with open('./data/ignou/courseInfo.txt', 'r') as file:
			lines = file.readlines()
			curSem = 0
			for line in lines:
				if len(line) < 2:
					curSem += 1
					continue
				words = line.split()
				if words[0] in subjects:
					requiredResponse.append((words[0], ' '.join(words[1:-1]), curSem, words[-1]))
		return requiredResponse

	def formatSubjectDetailResponse(self, subjectDetailResponse):
		requiredResponse = ''
		index = 1
		for subjectCode, subjectTitle, semester, credit in subjectDetailResponse:
			requiredResponse += f"**{index}.) {subjectCode} - {subjectTitle}**\n`(Sem{semester}), Credit-{credit}`\n"
			index+=1
		return requiredResponse

	async def getMarksResponse(self, dataParts):
		studentName = []
		session = None

		for dataPart in dataParts:
			if self.isValidSession(dataPart):
				session = dataPart
				continue
			studentName.append(dataPart)

		if len(studentName) < 1:
			return (1, None, "`Make sure to include Name or Enrolment!`")
		if session is None:
			return (1, None, None)

		studentName = " ".join(studentName)
		enrolmentNumber = await self.getEnrolmentNumber(studentName)
		studentName = await self.getStudentName(enrolmentNumber)

		if enrolmentNumber is None:
			if studentName == 'me':
				return (1, None, f"Couldn't get enrolment!\n\nTry saving your name using following syntax:\n{self.botNames[0]} saveme `Your Name`")
			return (1, None, "`Enrolment not found!`")

		marksResponse = await self.getMarks(enrolmentNumber, session)

		if len(marksResponse) < 1:
			return (1, None, "`Something went wrong!\nCheck your input and try again!`")

		marksResponse = self.formatMarksResponse(studentName, marksResponse)
		return (1, None, marksResponse)

	async def getMarks(self, enrolmentNumber, session):
		url = "https://termendresult.ignou.ac.in/TermEnd{}/TermEnd{}.asp".format(session.capitalize(), session.capitalize())
		params = {"eno":enrolmentNumber, "myhide":"OK"}

		urlResponse = requests.post(url, params = params, verify=False)
		htmlParser = BeautifulSoup(urlResponse.text, "html.parser")

		usefulData = [x.get_text() for x in htmlParser.find_all("strong")][1:]
		requiredData = []

		for i in range(0, len(usefulData), 5):
			requiredData.append((usefulData[i].strip(), usefulData[i+1].strip(), usefulData[i+2].strip()))

		return requiredData

	def formatMarksResponse(self, studentName, marksResponse):
		requiredResponse = f"Subject     Marks\n---------------------\n"
		for subject in marksResponse:
			requiredResponse += self.fillString(subject[0], " ", 12, 1)
			requiredResponse += self.fillString(subject[1], "0", 3, -1) + " (" + self.fillString(subject[2], "0", 3, -1) + ")"
			requiredResponse += "\n"
		requiredResponse = f"**{studentName}**\n\n" + "`" + requiredResponse + "`"
		return requiredResponse

	async def getResultResponse(self, dataParts):
		studentName = " ".join(dataParts)

		if len(studentName) < 1:
			return (1, None, "`Make sure to include Name or Enrolment!`")

		enrolmentNumber = await self.getEnrolmentNumber(studentName)
		if enrolmentNumber is None:
			if studentName == 'me':
				return (1, None, f"Couldn't get enrolment!\n\nTry saving your name using following syntax:\n{self.botNames[0]} saveme `Your Name`")
			return (1, None, "`Enrolment not found!`")

		resultResponse = await self.getResult(enrolmentNumber)

		if len(resultResponse) < 1:
			return (1, None, "`Something went wrong!\nCheck your input and try again!`")
		
		resultResponse = self.formatResultResponse(resultResponse)

		return (1, None, resultResponse)
	
	def calculatePercentage(self, subjects):
		obtainedMarks = 0
		totalMarks = 0
		for subject in subjects[1:]:
			if subject[0] in self.subjects_data['200']:
				obtainedMarks += round(int(subject[1]) * .5) + round(int(subject[3]) * 1.5)
				totalMarks += 200
				continue
			assMarks = int(subject[1]) if subject[1] != '-' else 0
			assMarks = (.25 * assMarks) if subject[0] not in self.subjects_data['ASS_30'] else (.3 * assMarks)
			if subject[2] == '-':
				teeMarks = int(subject[3]) if subject[3] != '-' else 0
			else:
				teeMarks = int(subject[2]) if subject[2] != '-' else 0
			teeMarks = (.75 * teeMarks) if subject[0] not in self.subjects_data['ASS_30'] else (.7 * teeMarks)

			if subject[0] in self.subjects_data['50']:
				teeMarks = round(teeMarks/2)
				assMarks = round(assMarks/2)
				obtainedMarks += teeMarks + assMarks
				if assMarks > 0 and teeMarks > 0:
					totalMarks += 50
				elif assMarks > 0:
					multiplier = .25 if subject[0] not in self.subjects_data['ASS_30'] else .3
					totalMarks += multiplier * 50
				elif teeMarks > 0:
					multiplier = .75 if subject[0] not in self.subjects_data['ASS_30'] else .7
					totalMarks += multiplier * 50
			else:
				teeMarks = round(teeMarks)
				assMarks = round(assMarks)
				obtainedMarks += assMarks + teeMarks
				if assMarks > 0 and teeMarks > 0:
					totalMarks += 100
				elif assMarks > 0:
					multiplier = .25 if subject[0] not in self.subjects_data['ASS_30'] else .3
					totalMarks += multiplier * 100
				elif teeMarks > 0:
					multiplier = .75 if subject[0] not in self.subjects_data['ASS_30'] else .7
					totalMarks += multiplier * 100
		percentage = (obtainedMarks / totalMarks) * 100
		return round(percentage, 2)
	
	async def getResult(self, enrolmentNumber, program = "BCA", typeProgram = 1):
		url = "https://gradecard.ignou.ac.in/gradecard/view_gradecard.aspx"
		params = {"eno":enrolmentNumber, "prog":program, "type": typeProgram}

		urlResponse = requests.post(url, params = params, verify=False)
		htmlParser = BeautifulSoup(urlResponse.text, "html.parser")

		studentName = htmlParser.find(id="ctl00_ContentPlaceHolder1_lblDispname").get_text()
		if len(studentName)==0:
			return []

		tables = htmlParser.find_all("table")
		dataTable = tables[-2]
		content = dataTable.find_all("font")
		content = [x.get_text() for x in content]
		requiredData = []
		percentageCalculations = [[], []]
		for i in range(9, len(content)-9, 9):
			subjectName = content[i]
			assignmentMarks = content[i+1] if subjectName not in self.subjects_data['200'] else content[i+2]
			termEndMarks = content[i+6]
			practicalMarks = content[i+7]
			passStatus = "☑️" if "NOT" in content[i+8] else "✅"  
			if assignmentMarks != "-":
				percentageCalculations[0].append(int(assignmentMarks))
			if termEndMarks != "-":
				percentageCalculations[1].append(int(termEndMarks))
			if practicalMarks != "-":
				percentageCalculations[1].append(int(practicalMarks))

			requiredData.append((subjectName, assignmentMarks, termEndMarks, practicalMarks, passStatus))

		percentage = self.calculatePercentage(requiredData)

		completeSemData = {1: {}, 2: {}, 3: {}, 4: {}, 5: {}, 6: {}}
		for subject in requiredData:
			for key, val in self.semester_subjects.items():
				if subject[0] in val:
					completeSemData[key][subject[0]] = subject
		for semester, semSubjects in completeSemData.items():
			if len(semSubjects) < 1: continue
			for subjectName, subjectData in semSubjects.items():
				subjectNameString = subjectData[0]
				assMarksString = subjectData[1]
				teeMarksString = subjectData[2] if subjectData[2] != '-' else subjectData[3]

				assMarks = int(assMarksString) if assMarksString != '-' else 0
				teeMarks = int(teeMarksString) if teeMarksString != '-' else 0
				obtainedMarks, maxMarks = self.getObtainedMarks(subjectNameString, assMarks, teeMarks)
				status = subjectData[4]

				completeSemData[semester][subjectName] = [assMarks, teeMarks, obtainedMarks, maxMarks, status]
		return studentName, completeSemData, percentage
	
	def getObtainedMarks(self, subjectName, assMarks, teeMarks):
		if subjectName in self.subjects_data['200']:
			obtainedMarks = round(assMarks * .5) + round(teeMarks * 1.5)
			# obtainedMarks = "{:.1f}".format(obtainedMarks)
			maxMarks = 200
			return obtainedMarks, maxMarks
		assMarks = (.25 * assMarks) if subjectName not in self.subjects_data['ASS_30'] else (.3 * assMarks)
		teeMarks = (.75 * teeMarks) if subjectName not in self.subjects_data['ASS_30'] else (.7 * teeMarks)

		if subjectName in self.subjects_data['50']:
			teeMarks /= 2
			assMarks /= 2
			obtainedMarks = round(teeMarks) + round(assMarks)
			maxMarks = 50
			return obtainedMarks, maxMarks
		else:
			obtainedMarks = round(assMarks) + round(teeMarks)
			maxMarks = 100
			return obtainedMarks, maxMarks

	def formatResultResponse(self, resultResponse):
		studentName, completeSemData, percentage = resultResponse
		requiredResponse = f"`Sub      A   T   Overall`\n"
		totalObtainedMarks = 0
		totalMaxMarks = 0
		for semesterNumber, semesterSubjects in completeSemData.items():
			if len(semesterSubjects) < 1: continue
			temp = self.fillString(f"Semester {semesterNumber}", " ", 25, 0)
			cur = '\n`' + " " * 6 + '`' + '**' + temp + '**' + '\n'
			obtainedSemesterMarks = 0
			maxSemesterMarks = 0
			for subjectName, subjectData in semesterSubjects.items():
				obtainedSemesterMarks += subjectData[2]
				maxSemesterMarks += subjectData[3]

				if subjectData[0] < 1:
					subjectData[0] = '-'
				if subjectData[1] < 1:
					subjectData[1] = '-'

				subjectNameString = self.fillString(subjectName, " ", 9, 1)
				assMarksString = self.fillString(f"{subjectData[0]}", " ", 4, 1)
				teeMarksString = self.fillString(f"{subjectData[1]}", " ", 4, 1)
				finalMarksString = self.fillString(f"{subjectData[2]}", " ", 3, -1) + '/' + self.fillString(f"{subjectData[3]}", " ", 4, 1)
				statusString = subjectData[4]
				
				cur += f"`{subjectNameString}{assMarksString}{teeMarksString}{finalMarksString}{statusString}`\n"
			totalObtainedMarks += obtainedSemesterMarks
			totalMaxMarks += maxSemesterMarks
			percentageSemester = "{:.2f}".format(((obtainedSemesterMarks/maxSemesterMarks)*100))
			requiredResponse += cur + '`' + self.fillString(f"{percentageSemester}% - {obtainedSemesterMarks}/{maxSemesterMarks}", " ", 24, -1) + '`' + '\n'
		
		totalMarks = "**Final**: __{}/{} ({}%)__".format(round(totalObtainedMarks), totalMaxMarks, percentage)
		requiredResponse = "**" + studentName + "**\n\n" + requiredResponse + '\n' + totalMarks# + '\n' + '**' + percentage + '**'
		return requiredResponse.strip()
	
	def getPrivateLeaderBoardResponse(self):
		leaderBoardResponse = self.getPrivateLeaderBoard()
		leaderBoardResponse = self.formatLeaderBoardResponse(leaderBoardResponse)
		return (1, None, leaderBoardResponse)
	
	def getPublicLeaderBoardResponse(self):
		leaderBoardResponse = self.getPublicLeaderBoard()
		leaderBoardResponse = self.formatLeaderBoardResponse(leaderBoardResponse, nameAdjustment=False)
		return (1, None, leaderBoardResponse)
	
	def formatLeaderBoardResponse(self, leaderBoardResponse, nameAdjustment=True, maxCount=50):
		requiredResponse = "🏆 **LEADERBOARD** 🏆\n\n"
		medals = ['🥇', '🥈', '🥉', '➖']
		for i, student in enumerate(leaderBoardResponse):
			studentName, percentage = student.split("-")
			if nameAdjustment:
				studentName = self.fillString(studentName.capitalize(), " ", 14, 1)
			requiredResponse += medals[min(3, i)] + f" `{studentName}- {percentage}%`\n" 
			maxCount -= 1
			if maxCount <= 0:
				break
		return requiredResponse
	
	def getPrivateLeaderBoard(self):
		with open("./data/ignou/privateLeaderboard.txt") as file:
			leaderBoard = file.read().strip().split('\n')
		return leaderBoard
	
	def getPublicLeaderBoard(self):
		with open("./data/ignou/publicLeaderboard.txt") as file:
			leaderBoard = file.read().strip().split('\n')
		for i in range(len(leaderBoard)):
			cur = []
			for word in leaderBoard[i].split():
				if '-' in word:
					cur.append(word[-6:])
				else:
					cur.append(word)
			leaderBoard[i] = " ".join(cur)
		return leaderBoard
	
	async def updatePrivateLeaderBoard(self):
		try:
			percentageData = dict()
			with open("./data/ignou/privateStudents.txt") as file:
				students = file.read().strip().split('\n')
			for student in students:
				enrolmentNumber = await self.getEnrolmentNumber(student)
				percentage = await self.getPercentage(enrolmentNumber)
				if percentage is None:
					continue
				percentageData[student] = percentage
			sortedPercentages = sorted(percentageData.items(), key=lambda x: x[1], reverse=True)
			leaderboard = ""
			for student, percentage in sortedPercentages:
				leaderboard += f"{student}-{percentage}\n"
			with open("./data/ignou/privateLeaderboard.txt", 'w') as file:
				file.write(leaderboard)
			return (1, None, f"`Leaderboard Updated!`")
		except Exception as e:
			return (1, None, f"An error occurred:\n{e}")
		
	async def updatePublicLeaderBoard(self):
		try:
			percentageData = dict()
			with open("./data/ignou/enrolments.txt") as file:
				students = file.read().strip().split('\n')
			for student in students:
				enrolmentNumber = student.split()[-1]
				try:
					percentage = await self.getPercentage(enrolmentNumber, validation=True)
					if percentage is None:
						continue
					percentageData[student] = percentage
					print(enrolmentNumber)
				except:
					print(f"{enrolmentNumber} FAILED!!")
					pass
			sortedPercentages = sorted(percentageData.items(), key=lambda x: x[1], reverse=True)
			leaderboard = ""
			for student, percentage in sortedPercentages:
				leaderboard += f"{student}-{percentage}\n"
			with open("./data/ignou/publicLeaderboard.txt", 'w') as file:
				file.write(leaderboard)
			return (1, None, f"`Public Leaderboard Updated!`")
		except Exception as e:
			return (1, None, f"An error occurred:\n{e}")
	
	def plot_semester_data(self, data, filename):
		"""
		Function to plot graphs from the provided data and save them as an image file.

		Parameters:
		- data: Dictionary containing data in the specified format.
		- filename: Name of the file to save the image.
		"""

		for serial_no, subjects in data.items():
			fig, axes = plt.subplots(nrows=len(subjects), ncols=1, figsize=(8, 6 * len(subjects)))

			for i, (subject, values) in enumerate(subjects.items()):
				x = range(1, len(values) + 1)
				y = values[:-1]  # Exclude binary data
				binary_data = values[-1]

				ax = axes[i] if len(subjects) > 1 else axes  # Handle multiple subplots

				ax.plot(x, y, marker='o', linestyle='-')
				ax.set_title(f'Subject: {subject}')
				ax.set_xlabel('Data Points')
				ax.set_ylabel('Values')
				ax.grid(True)

				if binary_data == 1:
					ax.annotate('Binary Data Present', xy=(0.5, 0.5), xycoords='axes fraction',
								xytext=(0.5, 0.5), textcoords='axes fraction',
								arrowprops=dict(facecolor='black', shrink=0.05),
								horizontalalignment='right', verticalalignment='top')

			plt.tight_layout()
			plt.savefig(f'{filename}_serial_{serial_no}_graph.png')
			plt.close()

	async def getEnrolmentResponse(self, dataParts):
		studentName = " ".join(dataParts)
		response = None
		if len(studentName) < 1:
			response = "`Invalid Input!`"
		else:
			enrolmentNumber = await self.getEnrolmentNumber(studentName)
			if enrolmentNumber is None:
				if studentName == 'me':
					response = f"Couldn't get enrolment!\n\nTry saving your name using following syntax:\n{self.botNames[0]} saveme `Your Name`"
				else:
					response = "`Not Found!`"
			else:
				response = '`'+enrolmentNumber+'`'
		return (1, None, response)

	async def getEnrolmentNumber(self, studentName):
		if studentName.isdigit():
			if len(studentName) < 9 or len(studentName) > 10:
				return None
			else:
				return studentName
		if studentName == 'me':
			studentName = await self.getNameFromTelegram()
			if studentName is None:
				return None
		enrolmentNumber = None
		with open("./data/ignou/enrolments.txt", "r") as file:
			lines = file.readlines()
			for line in lines:
				if studentName in line:
					enrolmentNumber = line.split()[-1]
					break
		return enrolmentNumber

	async def getNameResponse(self, dataParts):
		studentName = " ".join(dataParts)
		response = None
		if len(studentName) < 1:
			response = "`Invalid Input!`"
		else:
			enrolmentNumber = await self.getEnrolmentNumber(studentName)
			if enrolmentNumber is None:
				if studentName == 'me':
					response = f"Couldn't get enrolment!\n\nTry saving your name using following syntax:\n{self.botNames[0]} saveme `Your Name`"
				else:
					response = "`Not Found!`"
			else:
				studentName = await self.getStudentName(enrolmentNumber)
				if studentName is None:
					response = "`Not Found!`"
				else:
					response = '`'+studentName+'`'
		return (1, None, response)

	async def getStudentName(self, enrolmentNumber, program = "BCA", typeProgram = 1):
		url = "https://gradecard.ignou.ac.in/gradecard/view_gradecard.aspx"
		params = {"eno":enrolmentNumber, "prog":program, "type": typeProgram}

		urlResponse = requests.post(url, params = params, verify=False)
		htmlParser = BeautifulSoup(urlResponse.text, "html.parser")

		name = htmlParser.find(id="ctl00_ContentPlaceHolder1_lblDispname").get_text()
		if len(name)==0:
			return "Unknown"
		return name

	def isValidSession(self, session):
		if 6 >= len(session) >= 5 and session[-2:].isdigit():
			return True
		return False

	def isValidSubjectCode(self, code):
		if len(code) > 10 or len(code) < 4: return False
		if ('sem' in code.lower() and len(code) == 4) or code[-1].isdigit():
			return True
		return False

	def fillString(self, string, symbol, length, direction):
		string = string.strip()
		lengthDiff = length - len(string)
		if lengthDiff < 0:
			print("Length Overflow!")
		else:
			if direction > 0:
				string += symbol * lengthDiff
			elif direction < 0:
				string = symbol * lengthDiff + string
			else:
				string = symbol * (lengthDiff//2) + string + symbol * (lengthDiff//2)
		return string

	def getCommand(self, messageParts):
		command = None
		dataParts = []
		skipBotname = False
		for part in messageParts:
			curPart = part.strip()
			if curPart in self.botNames and not skipBotname: 
				skipBotname = True
				continue
			if curPart in self.possibleCommands:
				if command is None:
					command = curPart
					continue
			dataParts.append(curPart)
		return command, dataParts

	async def isMentioned(self):
		for botName in self.botNames:
			if botName in self.message.split(): return True
		return False
	
	#####################################

	async def updateDatesheet(self):
		import PyPDF2
		def isDate(string):
			if len(string) == 10 and string[2] in '/\\' and string[5] in '/\\':
				return True
			return False
		def isDay(string):
			return string.upper() in ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']
		def isCourseCode(string):
			if len(string) >= 4 and len(string) < 11 and string[-2:].isdigit() and string[:2].isalpha():
				return True
			return False
		# try:
		# datesheetURL = 'http://www.ignou.ac.in/userfiles/datesheet.pdf'
		# response = requests.get(datesheetURL, stream=True)
		# with open('./datesheet.pdf', 'wb') as fd:
		# 	for chunk in response.iter_content(2000):
		# 		fd.write(chunk)
		datesheetPDF = open('datesheet.pdf', 'rb')
		pdfReader = PyPDF2.PdfReader(datesheetPDF)
		with open('datesheetData.txt', 'w', encoding='utf-8') as file:
			curDate = None
			def handleWord(word, curDate):
				word = word.strip()
				if len(word) < 3: return curDate
				if isDate(word):
					curDate = word
					file.write(f"\n{curDate} ")
					return curDate
				if curDate is None: return curDate
				if isDay(word) or isCourseCode(word):
					file.write(f"{word} ")
				return curDate
			for i in range(0, len(pdfReader.pages)):
				for line in pdfReader.pages[i].extract_text().split('\n'):
					words = line.split()
					print(words)
					for word in words:
						if not isDate(word.strip()) and '/' in word:
							words2 = word.split('/')
							for word2 in words2:
								curDate = handleWord(word2, curDate)
						else:
							curDate = handleWord(word, curDate)

						
		# printing number of pages in pdf file
		# with open('tempTxt.txt', 'w', encoding='utf-8') as file:
		# 	file.write(pdfReader.pages[3].extract_text())
		# except:
		# 	print("Something went wrong!")
		# 	return 'Something Went Wrong!'
		print(pdfReader.pages)
		# for chunk in response.iter_content(2000):
		# 	print(chunk)
		# 	break

	def getAlternateSubjectCode(self, subject):
		for i in range(len(subject)):
			if subject[i].isdigit():
				if subject[i] == '0':
					return subject[:i] + subject[i+1:]
				else:
					return subject[:i] + '0' + subject[i:]
		return ''
