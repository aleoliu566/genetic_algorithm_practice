from statistics import *
from numpy import *
from random import *
from operator import itemgetter
from copy import deepcopy

# 0 日班 8人; 1 夜班 6人; 2 大夜班 4人; 3 放假

CROSSOVER_RATE = 0.8
MUTATION_RATE = 0.1
ITERATION_TIME = 3000    #迭代次數
NUMBER_OF_GENETIC = 200  #基因數量
NUMBER_OF_WORKER = 35    #工作人數
WORK_DAY = 28

# 染色體集合
all_genetic = []
best_genetic = []
best_genetic_target_value = 100000000000

def shiftScheduleScore(genetic, needToReachNumber, workType, showValue=False):
  score = 15
  shift_numbers = [0]*28

  # 記錄每天日班有多少人排班
  for i in range(len(genetic)):
    for j in range(WORK_DAY):
      if(genetic[i][j] == workType):
          shift_numbers[j] += 1

  day_did_not_reach_number = sum(i < needToReachNumber for i in shift_numbers)

  if showValue:
    print('沒有達到',needToReachNumber,'人的天數', day_did_not_reach_number)

  score = score * day_did_not_reach_number
  return score

# 判斷各種班別是否有達到上班人數標準，然後回傳一個分數
def three_work_type_score(teamSchedule,showValue):
  dayShiftScore = shiftScheduleScore(teamSchedule, 8, 0, showValue)
  laterShiftScore = shiftScheduleScore(teamSchedule, 6, 1, showValue)
  graveShiftScore = shiftScheduleScore(teamSchedule, 4, 2, showValue)

  score = dayShiftScore + laterShiftScore + graveShiftScore
  return score

def restrict_dayoff_work(genetic_list, number_of_worker, work_day, showValue):
  # 避免安排休假-工作-休假
  # 3 + (0,1,2) + 3

  penalty = 0
  count = 0
  for i in range(number_of_worker):
    for j in range(0,work_day-2):


      day1 = genetic_list[i][j]
      day2 = genetic_list[i][j+1]
      day3 = genetic_list[i][j+2]
      
      # 避免  3 - (0,1,2) - 3
      if (day1==3 and day3==3):
        if day2==3:
          pass
        else: # day2 == 0,1,2
          count += 1

  penalty = count * 1
  if(showValue):
    print('休假-工作-休假的次數：', count)
  return penalty

def restrict_night_day(genetic_list, number_of_worker, work_day, showValue):
  # 避免晚班-早班
  # (1,2) + 0

  count = 0
  for i in range(number_of_worker):
    for j in range(0,work_day-1):


      day1 = genetic_list[i][j]
      day2 = genetic_list[i][j+1]

      if (day1==1) or (day1==2):
        if day2==0:
          count += 1
  if(showValue):
    print('早班接晚班的次數：', count)
  penalty = count * 2
  return penalty

# 檢查員工一週最多工作6天和兩週最多工作11天
def check_each_worker_schedule_meet_the_law_of_labor(teamSchedule, showValue):
  score = 20
  NotMeetWorkerLawWeekNumber = 0   # 所有勞工沒有符合勞基法的週數

  everWeekWorkDay = 0
  everTwoWeekWorkDay = 0

  for i in range(NUMBER_OF_WORKER):
    for j in range(WORK_DAY):
      if(teamSchedule[i][j]!=3):
        everWeekWorkDay+=1
        everTwoWeekWorkDay+=1

      if((j+1)%7==0 and ((j+1)%2==0 or (j+1)%3==0) and j!=0): # 判斷14, 21, 28天
        if(everTwoWeekWorkDay>11):
          NotMeetWorkerLawWeekNumber += 1
        everTwoWeekWorkDay = everWeekWorkDay

      if((j+1)%7==0 and j!=0): # 檢查每個員工一週最多工作6天
        if(everWeekWorkDay>6):
          NotMeetWorkerLawWeekNumber+=1
        elif(everWeekWorkDay<2):
          NotMeetWorkerLawWeekNumber+=1
        everWeekWorkDay = 0
    everTwoWeekWorkDay = 0

  score = score * NotMeetWorkerLawWeekNumber
  if(showValue):
    print('在',NUMBER_OF_WORKER,'位勞工中，總共有',NotMeetWorkerLawWeekNumber,'週沒符合勞基法')
  return score

def targetFunction(teamSchedule, showValue=False):
  day_shift = [] #日班
  later_shift = []
  grave_shift = []
  day_off = []
  for i in range(NUMBER_OF_WORKER):
    day_shift.append(len([i for i in teamSchedule[i] if i == 0])) # 日班
    later_shift.append(len([i for i in teamSchedule[i] if i == 1])) # 夜班
    grave_shift.append(len([i for i in teamSchedule[i] if i == 2])) # 大夜班
    day_off.append(len([i for i in teamSchedule[i] if i == 3])) # 休假次數

  ShiftNumberBasicScore = three_work_type_score(teamSchedule,showValue)
  Penalty = restrict_dayoff_work(teamSchedule, NUMBER_OF_WORKER, WORK_DAY, showValue)+restrict_night_day(teamSchedule, NUMBER_OF_WORKER, WORK_DAY, showValue)
  LawOfJobPenalty = check_each_worker_schedule_meet_the_law_of_labor(teamSchedule, showValue)

  target_value = round(variance(day_shift)+variance(later_shift)+variance(grave_shift)+variance(day_off), 10) + ShiftNumberBasicScore + Penalty + LawOfJobPenalty
  if showValue:
    print('Total variance: ', target_value )
  return target_value


def crossover(): # 單點交配
  crossover_if = random()
  if( crossover_if > CROSSOVER_RATE): # 判斷是否要交配
    return
  else:
    # 隨機取兩個個體
    first = randint(0, NUMBER_OF_GENETIC-1)
    second = randint(0, NUMBER_OF_GENETIC-1)
    while(first==second):
      second = randint(0, NUMBER_OF_GENETIC-1)
    crossover_genetic_1 = all_genetic[first][:]
    crossover_genetic_2 = all_genetic[second][:]

    # 取得突變位置
    crossover_worker = int(random() * (NUMBER_OF_WORKER-1) ) # 取第幾個工人
    crossover_date = int(random() * (28-1) ) # 取工人第幾天的工作

    for i in range(crossover_date):
      temp = crossover_genetic_1[crossover_worker][i]
      crossover_genetic_1[crossover_worker][i] = crossover_genetic_2[crossover_worker][i]
      crossover_genetic_2[crossover_worker][i] = temp

    all_genetic[first] = deepcopy(crossover_genetic_1)
    all_genetic[second] = deepcopy(crossover_genetic_2)
  return

def muation(): # 每個染色體隨意找地方把一個值改成另一個
  global all_genetic
  muation_if = random()
  if( muation_if > MUTATION_RATE): # 判斷是否要突變
    return
  else:
    genetic_mutation = int(random() * (NUMBER_OF_GENETIC-1))
    worker_mutation = int(random() * (NUMBER_OF_WORKER-1))

    new_genetic = generateEachWorker()[:]
    all_genetic[genetic_mutation][worker_mutation] = new_genetic[:]
    return

# 生成母體必須符合：
# 1.員工一週最多工作6天(48小時)，最少2天-->休假數量最多=5(1周)
# 2.員工兩週最多工作11天
def generateEachWorker():
  each_worker = []
  work_type = 0
  workDay = 0 # 工作天數
  holiday = 0 # 休假數量
  twoWeeksWorkDay = 0 # 2個禮拜的工作天(第1、2周；第2、3周；第3、4周 三種可能)
  lastWeekWorkDay = 0

  for i in range(4):
    for j in range(7):

      if(holiday>=4):
        work_type = int(randint(0,2))
      elif(workDay>=6):
        work_type = int(randint(0,2))
        random_index = randrange(len(each_worker)-6, len(each_worker))
        each_worker[random_index] = 3
        holiday += 1
        workDay -= 1
      else: # random時給定一個比例
        type = [0, 0, 0, 0, 1, 1, 1, 2, 2, 3]
        work_type = choices( type )[0]

      if(work_type == 3):
        holiday += 1
      elif(work_type != 3):
        workDay +=1

      each_worker.append(work_type)

      if(i*7+j+1==14 or i*7+j+1==21 or i*7+j+1==28): # 第二週、第三週、第四週
        twoWeeksWorkDay = lastWeekWorkDay + workDay
        if(twoWeeksWorkDay > 11):
          for k in range(twoWeeksWorkDay - 11):
            random_index = randrange(len(each_worker)-6, len(each_worker))
            while(each_worker[random_index] == 3):
              random_index = randrange(len(each_worker)-6, len(each_worker))
            each_worker[random_index] = 3
            workDay -= 1
            holiday += 1

    lastWeekWorkDay = workDay
    workDay = 0
    holiday = 0
  return each_worker

def initializeGenetic():
  for i in range(NUMBER_OF_GENETIC):
    one_genetic = []
    for j in range(NUMBER_OF_WORKER):
      one_genetic.append(generateEachWorker()[:])
    all_genetic.append( one_genetic[:] )
    
    # 記錄最好的基因
    if(i == 0):
      best_genetic = one_genetic[:]
      best_genetic_target_value = targetFunction(best_genetic)
    elif(best_genetic_target_value > targetFunction(one_genetic) ):
      best_genetic = one_genetic[:]
      best_genetic_target_value = targetFunction(best_genetic)

def selectNextGeneration(number_of_generation):
  global all_genetic
  global best_genetic_target_value
  global best_genetic
  temp_all_genetic = []
  biggestTargetValue = -1
  population = []

  for j in range(NUMBER_OF_GENETIC):
    targetValue = targetFunction(all_genetic[j])
    population.append(targetValue)
    if(biggestTargetValue < targetValue):
      biggestTargetValue = targetValue

  # 如果全部基因都一樣沒有交配或突變就不用演進了
  different = True
  for i in range(1,len(population)):
    d = population[0]
    if(d!=population[i]):
      different = False

  if different:
    return

  for i in range(len(population)):
    population[i] = biggestTargetValue - population[i]

  for i in range(NUMBER_OF_GENETIC):
    x = choices( range(len(population)), population )
    temp_all_genetic.append(all_genetic[x[0]][:] )
  all_genetic = temp_all_genetic[:]

  for i in range(NUMBER_OF_GENETIC):
    targetValue = targetFunction(all_genetic[i])

    # 記錄最好的基因
    if(best_genetic_target_value > targetValue ):
      best_genetic = deepcopy(all_genetic[i])
      best_genetic_target_value = targetFunction(best_genetic)
  if(number_of_generation%10 == 0 or number_of_generation == 1):
    print('\n','======================= ITERATION ', number_of_generation ,' =======================')
    print('\n','----- Best Genetic Target Value: ', best_genetic_target_value, '-----')
    targetFunction(best_genetic, True)
  return

def main():
  initializeGenetic() # 初始化: 建立所有基因
  for i in range(ITERATION_TIME):
    selectNextGeneration(i+1) # 選擇: 選擇下一代基因
    for j in range(7):
      muation() # 突變 => 突變一點太小了，這邊直接突變一個工人的全部
    for j in range(7):
      crossover() # 交配

if __name__ == "__main__":
    main()