from bs4 import BeautifulSoup
import grequests, requests, datetime,time, re
from pathos.multiprocessing import ProcessingPool as Pool
import numpy as np
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, create_engine


#maybe get rid of the global at some point if possible
Base = declarative_base()

#define a class for the course data (rows of the courses table)
class Course(Base):
    __tablename__ = 'courselist'
    code = Column(String, primary_key=True)
    terms = Column(String)
    profs = Column(String)
    prereqs = Column(String)
    desc = Column(String)
    extend_existing=True
    def __repr__(self):
        return f'Course {self.code}'

#process the list of courselinks 
def scrapeCourseData(courseLinks, db='test.db'):
    #process each link on the page in parallel

    with Pool(processes=32) as pool:
        courseRequests = [grequests.get("https://www.mcgill.ca/" + course) for course in courseLinks]
        courseHtml = [response.text for response in grequests.map(courseRequests) if response != None and response.status_code == 200 ]
        pool.map(lambda x: procCourseSoup(x, db), courseHtml)


def scrapeCourseList(year="latest", debug=False):
    url = "https://www.mcgill.ca/study/"

    #get current year if no specific one is supplied
    if year == "latest":
        date = datetime.datetime.now()
        frame = date.year -1 if date.month < 5 else date.year
        url = url + str(frame) + '-' + str(frame+1) + "/courses/search"
    #else parse the year string
    else:
        yearSplit = year.split('-')

        #check for misformed argument
        if len(yearSplit) != 2:
            print("Error parsing year argument. Correct formatting is 'year-followingYear'. E.g. '2016-2017'")
            return []

        url = url + str(yearSplit[0]) + '-' + str(yearSplit[1]) + "/courses/search"

    #process first page separately since the url is different
    listHtml = requests.get(url).text
    listSoup = BeautifulSoup(listHtml, features='lxml')
    courseLinks = [x.a.get('href') for x in listSoup.findAll('h4', class_='field-content')]
    numpages = int(listSoup.find(class_='pager-last last').a.get('href').split('=')[-1])
    #numpages = 50
    numBatches = numpages // 16

    with Pool(processes=32) as pool:
        listRequests = [grequests.get(url + "?page=" + str(page)) for page in range(1,numpages)]
        listHtmls = [response.text for response in grequests.map(listRequests) if response != None and response.status_code == 200]
        for links in pool.map(procListHtml, listHtmls):
            courseLinks.extend(links)
    print("")
    return courseLinks

def procListHtml(html):
    soup = BeautifulSoup(html, features='lxml')
    links = [x.a.get('href') for x in soup.findAll('h4', class_='field-content')]
    return links

#process the course page data
def procCourseSoup(html, db):

    if html == None:
        return
    soup = BeautifulSoup(html, features='lxml')

    dbEngine = create_engine('sqlite:///' + db)

    courseTitle = soup.find(id='page-title').text.strip()
    courseCode = re.findall(r"\w+ \d+", courseTitle)[0]
    courseTitle = courseTitle.replace(courseCode + " ", "")

    courseTerms = soup.find(class_='catalog-terms').text.replace('Terms:','').strip()
    #split up the profs by term, we'll filter out the terms where the course is not scheduled later
    profsRaw = soup.find(class_='catalog-instructors').text.replace('Instructors:','').strip()
    courseProfsFall = re.findall(r"[\w,\s]+ \(Fall\)", profsRaw)[0].replace(' (Fall)', '') if 'Fall' in profsRaw else profsRaw
    courseProfsWinter = re.findall(r"[\w,\s]+ \(Winter\)", profsRaw)[0].replace(' (Winter)', '') if 'Winter' in profsRaw else profsRaw
    courseProfsSummer = re.findall(r"[\w,\s]+ \(Summer\)", profsRaw)[0].replace(' (Summer)', '') if 'Summer' in profsRaw else profsRaw

    #courseProfsSummer = [name.replace('(Summer)', '') for name in [cleanTuple(match) for match in re.findall(r"(,.* \(Summer\))|(\).* \(Summer\))|(^.* \(Summer\))", profsRaw)]]
    coursePrereqs = "None"

    #parse the notes section of the page to find the prereqs
    courseNotes = soup.find(class_="catalog-notes")
    if courseNotes:
        for note in courseNotes.children:
            para = courseNotes.find('p')
            if type(para) == int:
                return
            if "Prerequisite" in para.text or "Prerequisites" in para.text:
                coursePrereqs = para.text.replace("Prerequisites:", "").replace("Prerequisite:","").strip().replace(' and ', ',')
                break

    entry = Course( 
        code=courseCode,
        desc=courseTitle,
        terms=courseTerms,
        profs=str({
            'fall':courseProfsFall if 'Fall' in courseTerms else None,
            'winter':courseProfsWinter if 'Winter' in courseTerms else None,
            'summer':courseProfsSummer if 'Summer' in courseTerms else None,
            }),
        prereqs=coursePrereqs
    )
    print(entry.__dict__)
    #sql access
    session = sessionmaker(bind=dbEngine)()

    #check if the key exists
    exists = session.query(Course).filter(Course.code == entry.code).all()

    if exists:
        session.delete(*exists)
        session.add(entry)
    else:
        session.add(entry)

    print(entry)

    session.commit()
    session.close()

    return

        





