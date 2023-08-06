import warnings
warnings.filterwarnings("ignore")

class MessageHandler:
	def __init__(self):
		self.botName = "ritu"
		self.response = []
		self.possibleCommands = [
			"result", "marks", "grade", "grades", "gradecard", 
			"astatus", 
			"name",
			"centre",
			"enrolment", "enrol",
			"date", "datesheet",
			"sub", "subject",
			"saveme", "me",
			"commands", "command", "help"]
		self.subjects_data = {
			'50': ['FEG02', 'ECO01', 'BCSL013', 'ECO02', 'MCS013', 'MCS015', 'BCSL021', 'BCSL022', 'BCSL032', 'BCSL033', 'BCSL034', 'BCS040', 'BCS042', 'MCSL016', 'BCSL043', 'BCSL043', 'BCSL044', 'BCSL045', 'BCS053', 'BCS055', 'BCSL056', 'BCSL057', 'BCSL058', 'BCS062', 'BCSL063'],
			'ASS_30': ['FEG02', 'ECO01', 'ECO02'],
			'200': ['BCSP064']
		}

	async def handleMessage(self, event):
		self.message = event.message.message.lower()
		self.event = event
		# Check if mentioned, return if not
		mentioned = await self.isMentioned() or event.mentioned
		if not mentioned: 
			return []
		
		# Parse Message
		messageParts = self.message.split()

		# Check the command
		command, dataParts = self.getCommand(messageParts)

		# Return if command didn"t match
		if command is None:
			return []
		
		self.response = []

		# Perform action based on command
		if command in ["marks", "result", "grade", "gradecard", "grades"]:
			requiredResponse = await self.getMarksResponse(dataParts)
			if requiredResponse[-1] is None:
				requiredResponse = await self.getResultResponse(dataParts)
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
			requiredMessage += "**Possible Commands:**\n"
			requiredMessage += '`' + "\n".join(sorted(self.possibleCommands)) + '`'
			return [(1, None, requiredMessage)]
		
		elif command in ["me"]:
			requiredResponse = await self.getNameFromTelegramResponse()
			self.response.append(requiredResponse)

		# elif command in ["result"]:
		# 	resultResponse = await self.getResultResponse(dataParts)
		# 	self.response.append(resultResponse)


		return self.response
	
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
		import requests
		from bs4 import BeautifulSoup
		URL = f"https://admission.ignou.ac.in/changeadmdata/StatusExam.asp?submit=1&enrno={enrolmentNumber}&program=BCA"
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
			return (1, None, f"You're not in my record!\n\nTry saving your name using following syntax:\n{self.botName} saveme `Your Name`")
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
				return (1, None, f"Couldn't get enrolment!\n\nTry saving your name using following syntax:\n{self.botName} saveme `Your Name`")
			return (1, None, "`Enrolment not found!`")

		marksResponse = await self.getMarks(enrolmentNumber, session)

		if len(marksResponse) < 1:
			return (1, None, "`Something went wrong!\nCheck your input and try again!`")

		marksResponse = self.formatMarksResponse(studentName, marksResponse)
		return (1, None, marksResponse)

	async def getMarks(self, enrolmentNumber, session):
		import requests
		from bs4 import BeautifulSoup

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
				return (1, None, f"Couldn't get enrolment!\n\nTry saving your name using following syntax:\n{self.botName} saveme `Your Name`")
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
		print(obtainedMarks)
		print(totalMarks)
		percentage = (obtainedMarks / totalMarks) * 100
		return round(percentage, 2)
	
	async def getResult(self, enrolmentNumber, program = "BCA", typeProgram = 1):
		import requests
		from bs4 import BeautifulSoup

		url = "https://gradecard.ignou.ac.in/gradecard/view_gradecard.aspx"
		params = {"eno":enrolmentNumber, "prog":program, "type": typeProgram}

		urlResponse = requests.post(url, params = params, verify=False)
		htmlParser = BeautifulSoup(urlResponse.text, "html.parser")

		name = htmlParser.find(id="ctl00_ContentPlaceHolder1_lblDispname").get_text()
		if len(name)==0:
			return []

		tables = htmlParser.find_all("table")
		dataTable = tables[-2]
		content = dataTable.find_all("font")
		content = [x.get_text() for x in content]
		requiredData = [name]
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
		requiredData.append(f"Percentage: {percentage}")
		# requiredData.append("Percentage: {0:.2f}".format(
		# 	( ( sum(percentageCalculations[0]) / len(percentageCalculations[0]) ) * .25 +
    	# 	  ( sum(percentageCalculations[1]) / len(percentageCalculations[1]) ) * .75 )
		# ))
		return requiredData
		return "lol"

		data = ["`"+" ".join([x.capitalize() for x in name.split()])+"`", "", "`Sub         A    T    P`"]
		assignmentMarks = []
		teeMarks = []
		for i in range(9, len(content)-9, 9):
			data.append("`"+adjStr(content[i], dataAd[0]) + adjStr(content[i+1], dataAd[1]) + adjStr(content[i+6], dataAd[2]) + adjStr(content[i+7], dataAd[3])+"`")
			if not content[i+1]=="-":
				assignmentMarks.append(int(content[i+1]))
			if content[i+7]!="-":
				teeMarks.append(int(content[i+7]))
			elif content[i+6]!="-":
				teeMarks.append(int(content[i+6]))
			data[-1] += "☑️" if "NOT" in content[i+8] else "✅"
		if not len(teeMarks):
			percentage = "Not much data"#sum(assignmentMarks)/len(assignmentMarks)
		else:
			try:
				percentage = .25 ** (sum(assignmentMarks)/len(assignmentMarks)) + .75 ** (sum(teeMarks)/len(teeMarks))
			except:
				percentage = "Not much data"
		data.append("")
		data.append("`Percentage: {0:.2f}`".format(percentage))
		return "\n".join(data)
	
	def formatResultResponse(self, resultResponse):
		studentName = resultResponse[0]
		percentage = resultResponse[-1]
		requiredResponse = f"Sub       A   T   P   \n"
		for subject in resultResponse[1:][:-1]:
			cur = self.fillString(subject[0], " ", 10, 1)
			cur += self.fillString(subject[1], " ", 4, 1)
			cur += self.fillString(subject[2], " ", 4, 1)
			cur += self.fillString(subject[3], " ", 4, 1)
			cur += subject[4]
			cur += "\n"
			requiredResponse += cur
		requiredResponse = "**" + studentName + "**\n\n" + "`" + requiredResponse + "\n" + percentage + "`"
		return requiredResponse.strip()

	async def getEnrolmentResponse(self, dataParts):
		studentName = " ".join(dataParts)
		response = None
		if len(studentName) < 1:
			response = "`Invalid Input!`"
		else:
			enrolmentNumber = await self.getEnrolmentNumber(studentName)
			if enrolmentNumber is None:
				if studentName == 'me':
					response = f"Couldn't get enrolment!\n\nTry saving your name using following syntax:\n{self.botName} saveme `Your Name`"
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
					response = f"Couldn't get enrolment!\n\nTry saving your name using following syntax:\n{self.botName} saveme `Your Name`"
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
		import requests
		from bs4 import BeautifulSoup

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
		lengthDiff = length - len(string)
		if lengthDiff < 0:
			print("Length Overflow!")
		else:
			if direction > 0:
				string += symbol * lengthDiff
			elif direction < 0:
				string = symbol * lengthDiff + string
		return string

	def getCommand(self, messageParts):
		command = None
		dataParts = []
		skipBotname = False
		for part in messageParts:
			curPart = part.strip()
			if curPart == self.botName and not skipBotname: 
				skipBotname = True
				continue
			if curPart in self.possibleCommands:
				if command is None:
					command = curPart
					continue
			dataParts.append(curPart)
		return command, dataParts

	async def isMentioned(self):
		if self.botName in self.message.split(): return True
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
