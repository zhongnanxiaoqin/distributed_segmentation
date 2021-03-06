import queue,time
from multiprocessing.managers import BaseManager
from multiprocessing import Process,Queue

class QueueManager(BaseManager):
    pass

list_queue=queue.Queue()
task_queue=queue.Queue()
result_queue=queue.Queue()

def return_list_queue():
    global list_queue
    return list_queue

def return_task_queue():
    global task_queue
    return task_queue

def return_result_queue():
    global result_queue
    return result_queue

def read_word_freq_list():
    d = []
    with open('word_freq_list.utf8','r', encoding='utf-8') as fd:
        flists = fd.readlines()
        for flist in flists:
            s=''
            for i in range(len(flist)):
                if i>11 and flist[i]==' ':
                    break
                elif i>10:
                    s+=flist[i]
            d.append(s)
        lexicon = set(d)
        return  lexicon

def put_list(done_flag,lists,lexicon):
    while done_flag.empty():
        if lists.empty():
            lists.put(lexicon)
            print('\nput freq datas')

def close_worker(done_flag,task):
    while done_flag.empty():
        if task.empty():
            task.put('command:worker.close()')
            print('\nclose worker')


def break_for(matched,wordLen,sentence,startPoint,task,result,wordSeg):
    for i in range(wordLen, 0, -1):
        string = sentence[startPoint:startPoint+i]
        task.put(string)
        while True:
            try:
                r=result.get(timeout=2)
                if r:
                    print(string,end=' ')
                    wordSeg.append(string)
                    matched = True
                    startPoint+=len(string)
                    return matched,startPoint
                else:
                    break
            except queue.Empty:
                print('\nresult queue is empty now.')
                if task.empty():
                    task.put(string)
                continue
    return matched,startPoint

def start():
    done_flag=Queue()
    QueueManager.register('get_list_queue',callable=return_list_queue)
    QueueManager.register('get_task_queue',callable=return_task_queue)
    QueueManager.register('get_result_queue',callable=return_result_queue)
    manager=QueueManager(address=('127.0.0.1',8888),authkey=b'password')
    manager.start()
    lists=manager.get_list_queue()
    task=manager.get_task_queue()
    result=manager.get_result_queue()
    lexicon=read_word_freq_list()
    Plist=Process(target=put_list,args=(done_flag,lists,lexicon))
    Plist.start()
    wordSeg = []    # 新建列表存放切分好的词
    maxWordLen = 4  # 最大词长设为4
    with open('pku_test.utf8','r', encoding='utf-8') as src:
        sentence = src.read()
        sentenceLen = len(sentence)
        wordLen = min(maxWordLen, sentenceLen)
        startPoint = 0
        while startPoint < sentenceLen:  # 从第一个字符循环到最后一个字符
            matched=False
            matched,startPoint=break_for(matched,wordLen,sentence,startPoint,task,result,wordSeg)
            if not matched:    # 假如在词典中找不到匹配
                i = 1
                print(sentence[startPoint],end=' ')
                wordSeg.append(sentence[startPoint])   # 全部切分为单字词
                startPoint += i
    Pclose=Process(target=close_worker,args=(done_flag,task))
    Pclose.start()
    with open('WordSeg.txt', 'w', encoding='utf-8') as des:
        for word in wordSeg:
            des.write(word+'  ')
    done_flag.put('done')
    time.sleep(1)
    manager.shutdown()
    print('\nmaster exit.')

if __name__=='__main__':
    start()