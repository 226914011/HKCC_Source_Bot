import os, sys, threading, time #import lib

try:
	import requests #import lib
except ImportError:
	#install requests if missing
	print("Trying to Install required module: requests\n")
	os.system('python -m pip install requests')
	import requests

try:
	import bs4 #import lib
except ImportError:
	#install bs4 if missing
	print("Trying to Install required module: bs4\n")
	os.system('python -m pip install bs4')
	import bs4

from secret import username, password #import username and password

#User Ac default check
if username == "XXXXXXXXA" or password == "XXXXXXXXX":
	print("Please replace your username and password first.")
	exit(1)

#Preconfig
headers = {
    'User-Agent': 'User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0',
}

############################################################################################################################################################
#Login

url ='https://moodle.cpce-polyu.edu.hk/calendar/view.php?view=day'
session = requests.Session()

#get MoodleSessioncpcemoodle3
response = session.get(url=url,headers = headers, allow_redirects=False)
print(response.status_code)
MoodleSessioncpcemoodle3 = response.cookies.get_dict()

#get PHPSESSID
response = session.get(url='https://moodle.cpce-polyu.edu.hk/auth/saml/index.php',headers = headers, cookies = MoodleSessioncpcemoodle3,allow_redirects=False)
print(response.status_code)
PHPSESSID = response.cookies.get_dict()
data= response.text

soup=bs4.BeautifulSoup(data, "html.parser")
href=soup.find(id="redirlink")

#Combind cookie
ncookie = {**MoodleSessioncpcemoodle3, **PHPSESSID}
response = session.get(url = href.get('href'),headers = headers,cookies = ncookie,allow_redirects=False)
data=response.text

soup=bs4.BeautifulSoup(data, "html.parser")

#find data
LASTFOCUS = soup.find(id="__LASTFOCUS")
VIEWSTATE = soup.find(id="__VIEWSTATE")
VIEWSTATEGENERATOR = soup.find(id="__VIEWSTATEGENERATOR")
EVENTTARGET = soup.find(id="__EVENTTARGET")
EVENTVALIDATION = soup.find(id="__EVENTVALIDATION")
SAMLRequest =  soup.find(id="aspnetForm")
SAMLRequest.get('value')

data = {
	"__LASTFOCUS": LASTFOCUS.get('value'),
	"__VIEWSTATE": VIEWSTATE.get('value'),
	"__VIEWSTATEGENERATOR": VIEWSTATEGENERATOR.get('value'),
	"__EVENTTARGET": EVENTTARGET.get('value'),
	"__EVENTVALIDATION": EVENTVALIDATION.get('value'),
	"__db": "15",
	"ctl00$ContentPlaceHolder1$UsernameTextBox": username,
	"ctl00$ContentPlaceHolder1$PasswordTextBox": password,
	"ctl00$ContentPlaceHolder1$SubmitButton": "Sign+In",
	"ctl00$ContentPlaceHolder1$UserAccountControlWSText": "",
	"ctl00$ContentPlaceHolder1$UserUPNWSText": "",
	"ctl00$ContentPlaceHolder1$ADFSDevVersion": "1.1.6862.25998"
}

#Post the Ac Info
result = session.post(url="https://adfs.cpce-polyu.edu.hk/"+ SAMLRequest.get('action'),headers = headers,data=data,allow_redirects=False)

#Get the MSISAuthenticated,MSISLoopDetectionCookie,SamlSession
cdict = result.cookies.get_dict()

result2 = session.post(url="https://adfs.cpce-polyu.edu.hk/"+ SAMLRequest.get('action'),headers = headers,cookies = cdict,allow_redirects=False)
print(result2.status_code)


data= result2.text
soup=bs4.BeautifulSoup(data, "html.parser")
SAMLResponse = soup.find("input",{"name":"SAMLResponse"})
RelayState = soup.find("input",{"name":"RelayState"})

#User Ac Validation Check
if SAMLResponse is None:
	print("Username or password invalid,please try agin.")
	print()
	exit(1)

data = {
	"SAMLResponse": SAMLResponse.get('value'),
	"RelayState": RelayState.get('value'),
}

result3 = session.post(url= 'https://moodle.cpce-polyu.edu.hk/simplesaml/module.php/saml/sp/saml2-acs.php/moodlesso', cookies=ncookie,data = data,allow_redirects=False)
print(result3.status_code)

#merge required cookies
cookie = {**ncookie, **result3.cookies.get_dict()}
result4 = session.post(url= 'https://moodle.cpce-polyu.edu.hk/auth/saml/index.php', cookies=cookie,allow_redirects=False)
print(result4.status_code)

cjdict = result4.cookies.get_dict()

result5 = session.post(url= 'https://moodle.cpce-polyu.edu.hk', cookies=cjdict)
print(result5.status_code)
if result5.status_code == 200:
	print("Login successful!")
	print()
else:
	print("Login unsuccessful!")
	print()
	exit(1)

############################################################################################################################################################
#Select resource url

result6 = session.post(url= 'https://moodle.cpce-polyu.edu.hk', cookies=cjdict)

print(result6.status_code)

data = result6.text
soup=bs4.BeautifulSoup(data, "html.parser")

subcategories = soup.find_all("div",{"class":"category loaded with_children collapsed"},{"data-depth":"3"})

if subcategories == None:
	print("Error: Subcategories not found!")
	exit(1)

############################################################################################################################################################
#Get resource

def dec(x):
	return bytes(bytes.fromhex(x)).decode('utf-8')

#this is "/" in hex format
chr = dec("2F")

def rmunwrchr(stringfile):
	#Check if unwritable characters are in filename
	unwchar = [dec("5C") , dec("2F"),dec("3A"),dec("2A"),dec("3F"),dec("22"),dec("3C"),dec("3E"),dec("7C"),'.pdf', '.doc', '.docx','.mp4','.cpp', '.mp3']
	matchs = [x for x in unwchar if x in stringfile]
	if any(matchs):
		for match in matchs:
			buffer = ""
			for name in stringfile.split(str(match)):
				buffer += name
			stringfile = buffer
	return stringfile


#get file in filtered link
def getFiles(link,cjdict,classname,SAVE_PATH):
	r = requests.get(url = link['href'], cookies=cjdict, allow_redirects=True)

	#resolve pop up resource
	if r.url.find("https://moodle.cpce-polyu.edu.hk/mod/resource/view.php?id=") == 0:
		data = r.text
		soup=bs4.BeautifulSoup(data, "html.parser")
		rlinks = soup.find("div",{"class":"resourceworkaround"})
		try:
			rlink = rlinks.find("a",href = True, onclick = True)
		except:
			print("Unexpected error:", sys.exc_info())
			#some bug here waiting to be fix
			return
		r = session.get(url = rlink['href'], cookies=cjdict, allow_redirects=True, timeout=None)
	
	if r.headers.get('content-type') is not None:
		#class for filename
		if classname == "fp-filename":
			filename_header = link.find("span",{"class":classname}).text
		else:
			filename_header = link.find("span",{"class":classname}).text[:-5]

		filename_header = rmunwrchr(filename_header)
		filename_type = "."+ r.headers.get('content-disposition').rsplit(".",1)[1][:-1]

		filename = filename_header + filename_type
		filepath = SAVE_PATH + chr + filename
		for i in range(10):
			if os.path.isfile(filepath):
				a = filename.rsplit(".",1)
				filepath = SAVE_PATH + chr + a[0] + "(" + str(i+1) + ")." +a[1]
				break
			else:
				i +=1
		print(filepath)
		print()
		open(filepath, 'wb').write(r.content)
	else:
		print("Potentially a bug, please report to the author if possible")

def CreateFolder(SAVE_PATH):
	if not os.path.exists(SAVE_PATH):
		os.makedirs(SAVE_PATH)
		print(f"Created folder{SAVE_PATH}")
		print()


while(True):
	urlss = []
	hrefs = []
	thread_lists = []

	i = 1
	print("0 . Select All")
	for s in subcategories:
		print(i,".",s.find("h4",{"class":"categoryname"}).text)
		i += 1
		hrefs = s.find_all("a",{"class":""}, href=True)
		url = []
		for href in hrefs:
			if href['href'].find("https://moodle.cpce-polyu.edu.hk/course/view.php?") == -1:
				continue
			else:
				url.append(href['href'])
		urlss.append(url)

	print()
	print('Enter the number of data you want:')
	x = int(input())

	if x != 0:
		urlss = [urlss[x-1]]

#start download the files with multi-thread
	#time counting
	start = time.time()
	for urls in urlss:
		for url in urls:
			result7 = session.post(url= url, cookies=cjdict,allow_redirects=True)
			data = result7.text
			soup=bs4.BeautifulSoup(data, "html.parser")
			print(result7.status_code,result7.url)
			print()

			cfolder = rmunwrchr(str(soup.title).split(":")[1][:-8])
			SAVE_PATH = os.getcwd() + chr + "file" + chr + cfolder
			CreateFolder(SAVE_PATH)

			#two format of resources
			#capture viedos in urls are not done
			files = soup.find_all("li",{"class":"activity resource modtype_resource"})
			folders = soup.find_all("li",{"class":"activity folder modtype_folder"})

			if not len(files) and not len(folders):
				print("Folder is empty")
				time.sleep(0.5) #delay 0.5s
				os.rmdir(SAVE_PATH)

			#Download Files
			for file in files:
				links = file.find_all("a",href = True)
				for link in links:
					if link['href'].find("https://moodle.cpce-polyu.edu.hk/mod/resource/view.php?id=") == 0:
						mp4 = link.find_all("img",{"src":"https://moodle.cpce-polyu.edu.hk/theme/image.php/boost/core/1613055348/f/mpeg-24"})

						png = link.find_all("img",{"src":"https://moodle.cpce-polyu.edu.hk/theme/image.php/boost/core/1613055348/f/png-24"}) + link.find_all("img",{"src":"https://moodle.cpce-polyu.edu.hk/theme/image.php/boost/core/1631325651/f/png-24"})

						jpeg = link.find_all("img",{"src":"https://moodle.cpce-polyu.edu.hk/theme/image.php/boost/core/1613055348/f/jpeg-24"}) + link.find_all("img",{"src":"https://moodle.cpce-polyu.edu.hk/theme/image.php/boost/core/1625564560/f/jpeg-24"})

						html = link.find_all("img",{"src":"https://moodle.cpce-polyu.edu.hk/theme/image.php/boost/core/1625564560/f/html-24"})
						
						if mp4:
							#mp4 file 
							print(mp4)
							print("Mp4 file,pass")
							print()
						elif png or jpeg:
							#img file
							print(png,jpeg)
							print("Img file,pass")
							print()
						elif html:
							#html file
							print(html)
							print("html file,pass")
							print()
						else:	
							try:
								thread = threading.Thread(target=getFiles, args=(link,cjdict,"instancename",SAVE_PATH))
								thread.setDaemon(True)
								thread.start()
								thread_lists.append(thread)
							except:
								print("Unexpected error:", sys.exc_info())
								print(link,SAVE_PATH)
								print()

			#Download Folder no needs to open link
			for folder in folders:
				withoutlink = folder.find_all("div",{"class":"contentwithoutlink"})
				if withoutlink:
					foldername = rmunwrchr(withoutlink[0].find("img",{"src":"https://moodle.cpce-polyu.edu.hk/theme/image.php/boost/core/1613055348/f/folder-24"}).get('title'))
					Folder_SAVE_PATH = SAVE_PATH + chr + foldername
					CreateFolder(Folder_SAVE_PATH)

					links = withoutlink[0].find_all("a",href = True)
					for link in links:
						if link['href'].find("https://moodle.cpce-polyu.edu.hk/pluginfile.php/") == 0:
								thread = threading.Thread(target=getFiles, args=(link,cjdict,"fp-filename",Folder_SAVE_PATH))
								thread.setDaemon(True)
								thread.start()
								thread_lists.append(thread)

			#Download Folder needs open link
				else:
					foldername = rmunwrchr(folder.find("span",{"class":"instancename"}).text[:-7])
					Folder_SAVE_PATH = SAVE_PATH + chr + foldername
					CreateFolder(Folder_SAVE_PATH)
					
					withlink = folder.find_all("div",{"class":"activityinstance"})

					flinks = withlink[0].find_all("a",href = True)
					for flink in flinks:
						if flink['href'].find("https://moodle.cpce-polyu.edu.hk/mod/folder/view.php?") == 0:
							r = requests.get(url = flink['href'], cookies=cjdict, allow_redirects=True)
							data = r.text
							soup=bs4.BeautifulSoup(data, "html.parser")
							withoutlink = soup.find_all("div",{"id":"folder_tree0"},{"class":"filemanager"})

							links = withoutlink[0].find_all("a",href = True)
							for link in links:
								if link['href'].find("https://moodle.cpce-polyu.edu.hk/pluginfile.php/") == 0:
									thread = threading.Thread(target=getFiles, args=(link,cjdict,"fp-filename",Folder_SAVE_PATH))
									thread.setDaemon(True)
									thread.start()
									thread_lists.append(thread)

	for thread in thread_lists:
		thread.join()

	stop = time.time()
	print()
	print(f"Finished with time: {stop - start}")
	print("Input q to exit or else continue")
	x = input()
	if x == "q":
		break