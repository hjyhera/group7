import requests
from bs4 import BeautifulSoup
import pickle

#페이지 내에서 체류자격 상담 건의 상담 번호 뽑아내는 함수
def extractNum(pageNum):
  res = requests.get("https://gmhr.or.kr/case?page="+ str(pageNum))

  soup = BeautifulSoup(res.content, 'html.parser')

  content1 = soup.find('div', class_='tbl_head01 tbl_wrap')
  content2 = content1.find_all('td', class_='td_num2')
  content3 = content1.find_all('a')

  classification=[]
  consultingNum =[]
  result=[]

  # 현재 목록에서 상담 번호 뽑아내기
  for i in content2:
    string = i.get_text()
    word = string.strip()
    consultingNum.append(word)
  #print(classification)

  #현재 목록에서 상담 유형 뽑아내기
  j=0
  for i in content3:
    j+=1
    if j%2==1:
      string = i.get_text()
      word = string.strip()
      classification.append(word)


  j=0
  for i in classification:
    if i == '체류자격': result.append((int(consultingNum[j]),pageNum))
    j+=1

  #result 리스트에는 상담유형이 체류자격인 상담 번호와 페이지 번호로 구성된 튜플이 들어있음
  #print(result)

  return result

#상담사례 페이지에서 상담 내용을 뽑아내는 함수
def extractContent(consultingNum, pageNum):
  num1 = int(consultingNum) + 3
  num2 = pageNum


  #html 페이지 요청(res에 html 데이터 저장)
  res = requests.get("https://gmhr.or.kr/case/" + str(num1) + "?page=" + str(num2))


  #html 페이지 파싱
  soup = BeautifulSoup(res.content, 'html.parser')

  #필요한 데이터 검색
  content0 = soup.find('span', class_='bo_v_tit')
  content1 = soup.find('table', class_='consult-tbl')
  content2 = content1.find_all('td', colspan = '4')

   #필요한 데이터 추출(페이지 내에서 상담 내용/ 진행과정 및 결과를 뽑아내는 건 성공)
  title = content0.get_text().strip()
  consulting = content2[0].get_text().strip()
  result = content2[1].get_text().strip()
  law = content2[2].get_text().strip()
  evaluation = content2[3].get_text().strip()

  #print("상담 내용: \n", consulting)
  #print("\n")
  #print("진행 과정 및 결과: \n",result)

  
  returnresult = (consulting,result,law,evaluation)
  return (title, returnresult)







# extract consulting case number and page number
# return form : [(case number1, page number1), ... , (case number n, page number n)]
# example(i=3) : [(1676, 2), (1680, 2), (1687, 1), (1698, 1), (1700, 1)]
NumList = []
for i in range(115):
  if i == 0 : continue
  result = extractNum(i)
  NumList= NumList + result
  NumList.sort(key = lambda x : x[0])


# extract 상담 제목, 내용, 과정, 관련법률, 평가
cstdict = {}
num = len(NumList)
for i in range(num):
  cstnum = NumList[i][0]               #NumList[i][0] 도 작동 잘 되는디
  pagenum = NumList[i][1]
  title, returnresult = extractContent(cstnum,pagenum)
  cstdict[title] = returnresult

#1,2 페이지에 있는 체류자격 상담 사례 중에서 상담 번호가 앞번호인 것부터 3개만 뽑아줌
#얘를 파일에 어떻게 넣을건지는 고민

#print(cstdict.keys())

#title, returnresult = extractContent(1680, 2)
#cstdict={}
#cstdict[title] = returnresult
#print(cstdict[title])


with open("crawling_data.pickle", "wb") as f:
    pickle.dump(cstdict, f)