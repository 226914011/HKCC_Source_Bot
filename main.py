import requests #import lib
from secret import username, password #import username and password

#Preconfig
headers = {
    'User-Agent': 'User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0',
}


############################################################################################################################################################
#Login

url ='https://moodle.cpce-polyu.edu.hk/calendar/view.php?view=day'
session = requests.Session()


#load MOODLEID1_cpcemoodle3 in local
import browser_cookie3
cj = browser_cookie3.load(domain_name='moodle.cpce-polyu.edu.hk')
MOODLEID1_cpcemoodle3 = {c.name:c.value for c in cj}

#get MoodleSessioncpcemoodle3
response = session.get(url=url,headers = headers, cookies = MOODLEID1_cpcemoodle3,allow_redirects=False)
print(response.status_code)
MoodleSessioncpcemoodle3 = response.cookies.get_dict()

#merge MOODLEID1_cpcemoodle3 with MoodleSessioncpcemoodle3
cookie = {**MOODLEID1_cpcemoodle3, **MoodleSessioncpcemoodle3}

response = session.get(url='https://moodle.cpce-polyu.edu.hk/auth/saml/index.php',headers = headers, cookies = cookie,allow_redirects=False)
print(response.status_code)
PHPSESSID = response.cookies.get_dict()
data= response.text

import bs4
soup=bs4.BeautifulSoup(data, "html.parser")
href=soup.find(id="redirlink")

ncookie = {**MOODLEID1_cpcemoodle3, **MoodleSessioncpcemoodle3, **PHPSESSID}
response = session.get(url = href.get('href'),headers = headers,cookies =ncookie,allow_redirects=False)
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

data = {
	"SAMLResponse": SAMLResponse.get('value'),
	"RelayState": RelayState.get('value'),
}

result3 = requests.post(url= 'https://moodle.cpce-polyu.edu.hk/simplesaml/module.php/saml/sp/saml2-acs.php/moodlesso', cookies=ncookie,data = data,allow_redirects=False)
print(result3.status_code)

#merge required cookies
cookie = {**ncookie, **result3.cookies.get_dict()}
result4 = requests.post(url= 'https://moodle.cpce-polyu.edu.hk/auth/saml/index.php', cookies=cookie,allow_redirects=False)
print(result4.status_code)

cjdict = result4.cookies.get_dict()

result5 = requests.post(url= 'https://moodle.cpce-polyu.edu.hk', cookies=cjdict)
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

result6 = requests.post(url= 'https://moodle.cpce-polyu.edu.hk', cookies=cjdict)

print(result6.status_code)

data = result6.text
soup=bs4.BeautifulSoup(data, "html.parser")

subcategories = soup.find_all("div",{"class":"category loaded with_children collapsed"},{"data-depth":"3"})

if subcategories == None:
	print("Error: Subcategories not found!")
	exit(1)

############################################################################################################################################################
#Get resource

import os
import base64

def dec(x):
	return bytes(bytes.fromhex(x)).decode('utf-8')

#this is "/" in hex format
chr = dec("2F")

#get file in filtered link
def getFiles(link,cjdict,classname,SAVE_PATH):
	r = requests.get(url = link['href'], cookies=cjdict, allow_redirects=True)
	if r.headers.get('content-type') is not None:
		#class for filename
		print(link.find("span",{"class":classname}))
		if classname == "fp-filename":
			filename_header = link.find("span",{"class":classname}).text
		else:
			filename_header = link.find("span",{"class":classname}).text[:-5]
		
		#Check if unwritable characters are in filename
		unwchar = [dec("5C") , dec("2F"),dec("3A"),dec("2A"),dec("3F"),dec("22"),dec("3C"),dec("3E"),dec("7C"),'.pdf', '.doc', '.docx','.mp4','.cpp']
		matchs = [x for x in unwchar if x in filename_header]
		if any(matchs):
			for match in matchs:
				buffer = ""
				for name in filename_header.split(str(match)):
					buffer += name
				filename_header = buffer
		print(r.headers.get('content-disposition'))
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

def CreateFolder(SAVE_PATH):
	if not os.path.exists(SAVE_PATH):
		os.makedirs(SAVE_PATH)
		print(f"Created folder{SAVE_PATH}")
		print()


while(True):
	urls = []
	hrefs = []

	i = 1
	print("0 . Select All")
	for s in subcategories:
		print(i,".",s.find("h4",{"class":"categoryname"}).text)
		i += 1
		hrefs = s.find_all("a",{"class":""}, href=True)
		url = []
		for href in hrefs:
			#print(href)
			if href['href'].find("https://moodle.cpce-polyu.edu.hk/course/view.php?") == -1:
				continue
			else:
				url.append(href['href'])
				#print(url)
		urls.append(url)
		#print(urls[i-1])
		#print()

	print()
	print('Enter the number of data you want:')
	x = int(input())

	if x != 0:
		urls = urls[x-1]

	for url in urls:
		result7 = requests.post(url= url, cookies=cjdict,allow_redirects=True)
		data = result7.text
		soup=bs4.BeautifulSoup(data, "html.parser")
		print(result7.status_code,result7.url)
		print()

		cfolder = str(soup.title).split(":")[1][:-8]
		SAVE_PATH = os.getcwd() + chr + "file" + chr + cfolder
		CreateFolder(SAVE_PATH)

		#two format of resources
		#capture viedos in urls are not done
		files = soup.find_all("li",{"class":"activity resource modtype_resource"})
		folders = soup.find_all("li",{"class":"activity folder modtype_folder"})

		if not len(files) and not len(folders): 
			print("Folder is empty")
			os.rmdir(SAVE_PATH)

	#Download Files
		for file in files:
			links = file.find_all("a",href = True)
			for link in links:
				if link['href'].find("https://moodle.cpce-polyu.edu.hk/mod/resource/view.php?id=") == 0:
					print(link)
					mp4 = link.find_all("img",{"src":"https://moodle.cpce-polyu.edu.hk/theme/image.php/boost/core/1613055348/f/mpeg-24"})
					img1 = link.find_all("img",{"src":"https://moodle.cpce-polyu.edu.hk/theme/image.php/boost/core/1613055348/f/png-24"})
					img2 = link.find_all("img",{"src":"https://moodle.cpce-polyu.edu.hk/theme/image.php/boost/core/1613055348/f/jpeg-24"})
					if mp4:
						#mp4 file 
						print(mp4)
						print("Mp4 file,pass")
						print()
					elif img1 or img2:
						#img file
						print(img1,img2)
						print("Img file,pass")
						print()
					else:	
						try:
							getFiles(link,cjdict,"instancename",SAVE_PATH)
						except:
							print("An exception occurred")
							print()



	#Download Folder with link
		for folder in folders:
			withoutlink = folder.find_all("div",{"id":"folder_tree0"},{"class":"filemanager"})
			if withoutlink:
				print(withoutlink[0])
				print()
				foldername = withoutlink[0].find("img",{"src":"https://moodle.cpce-polyu.edu.hk/theme/image.php/boost/core/1613055348/f/folder-24"}).title
				Folder_SAVE_PATH = SAVE_PATH + chr + foldername
				CreateFolder(Folder_SAVE_PATH)

				links = withoutlink[0].find_all("a",href = True)
				for link in links:
					if link['href'].find("https://moodle.cpce-polyu.edu.hk/pluginfile.php/") == 0:
						getFiles(link,cjdict,"fp-filename",Folder_SAVE_PATH)
						
	#Download Folder without link
			else:
				foldername = folder.find("span",{"class":"instancename"}).text[:-7]
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
								getFiles(link,cjdict,"fp-filename",Folder_SAVE_PATH)
	print()
	print("Finished")
	print("Input q to exit or else continue")
	x = input()
	if x == "q":
		break