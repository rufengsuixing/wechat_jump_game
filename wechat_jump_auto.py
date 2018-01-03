# coding: utf-8
'''
# === 思路 ===
# 核心：每次落稳之后截图，根据截图算出棋子的坐标和下一个块顶面的假中点坐标，
#      根据两个点的x距离乘以一个自动计算的时间系数获得长按的时间
# 识别棋子：靠棋子的颜色来识别位置，从下到上50*100随机取点，找两个边缘点
#      
# 识别棋盘：靠底色和方块的色差来做，从棋子开始，斜着最远点获得一个点，水平寻找第二个点，中点坐标当作x距离
# 最后：根据x坐标差乘以系数来获取长按时间
'''
import os
import sys
import subprocess
import time
import math
from PIL import Image
import random
from six.moves import input
try:
    from common import debug, config
except ImportError:
    print('请在项目根目录中运行脚本')
    exit(-1)


VERSION = "1.1.1"


debug_switch = True    # debug 开关，需要调试的时候请改为：True
#config = config.open_accordant_config()
press_coefficient=0

screenshot_way = 2

def get_magicnumber():
    pull_screenshot()
    im = Image.open('./autojump.png')
    # 获取棋子和 board 的位置
    xcha1 = find_piece_and_board(im)
    set_button_position(im)
    jump(0) #100ms
    time.sleep(1)
    pull_screenshot()
    im = Image.open('./autojump.png')
    # 获取棋子和 board 的位置
    xcha2 = find_piece_and_board(im)
    global press_coefficient
    press_coefficient=100/(xcha1-xcha2) #100ms 的距离
    

def pull_screenshot():
    '''
    新的方法请根据效率及适用性由高到低排序
    '''
    global screenshot_way
    if screenshot_way == 2 or screenshot_way == 1:
        process = subprocess.Popen('adb shell screencap -p', shell=True, stdout=subprocess.PIPE)
        screenshot = process.stdout.read()
        if screenshot_way == 2:
            binary_screenshot = screenshot.replace(b'\r\n', b'\n')
        else:
            binary_screenshot = screenshot.replace(b'\r\r\n', b'\n')
        f = open('autojump.png', 'wb')
        f.write(binary_screenshot)
        f.close()
    elif screenshot_way == 0:
        os.system('adb shell screencap -p /sdcard/autojump.png')
        os.system('adb pull /sdcard/autojump.png .')


def set_button_position(im):
    '''
    将 swipe 设置为 `再来一局` 按钮的位置
    '''
    global swipe_x1, swipe_y1, swipe_x2, swipe_y2
    w, h = im.size
    left = int(w / 2)
    top = int(1584 * (h / 1920.0))
    left = int(random.uniform(left-50, left+50))
    top = int(random.uniform(top-10, top+10))    # 随机防 ban
    swipe_x1, swipe_y1, swipe_x2, swipe_y2 = left, top, left, top


def jump(distance):
    '''
    跳跃一定的距离
    '''
    press_time = distance * press_coefficient
    press_time = max(press_time, 100)   # 设置 100ms 是最小的按压时间
    press_time = int(press_time)
    cmd = 'adb shell input swipe {x1} {y1} {x2} {y2} {duration}'.format(
        x1=swipe_x1,
        y1=swipe_y1,
        x2=swipe_x2,
        y2=swipe_y2,
        duration=press_time
    )
    print(cmd)
    os.system(cmd)
    return press_time

def pipei(l1,l2,cha):
    for a in range(0,len(l1)):
        if abs(l1[a]-l2[a])>cha:
            return False
    return True
            
def find_piece_and_board(im):
    '''
    寻找关键坐标
    '''
    w, h = im.size

    piece_x= 0
    piece_y = 0
    board_x = 0
    board_y = 0
    scan_x_border = int(w / 8)  # 扫描棋子时的左右边界
    scan_start_y = int(h/3)  # 扫描的起始 y 坐标
    scan_stop_y = int(h*2/3)  # 扫描的终止 y 坐标
    scan_start_x = int(w/9)  # 扫描的起始 x 坐标
    scan_stop_x = int(w*8/9)  # 扫描的终止 y 坐标
    im_pixel = im.load()
    #get 图片中一个紫色坐标
    for x in range(scan_stop_x,scan_start_x,-50):
        for y in range(scan_stop_y,scan_start_y,-100):
            if pipei([57,50,89],im_pixel[x,y],19):
                break
        else:
            continue
        break
    #print('qizi',x,y)
    #get 左边缘
    for x1 in range(x,scan_start_x,-1):
        if not pipei([57,50,89],im_pixel[x1,y],19):
                for yp in range(-10,15,1):
                    if pipei([57,50,89],im_pixel[x1,y+yp],19):
                        y=y+yp
                        break
                else:
                    break
    x=x1+1
    for y1 in range(y,y+10,1):
        if not pipei([57,50,89],im_pixel[x,y1],19):
            break
    y=y1-1
    #get 右边缘
    for x1 in range(x,scan_stop_x,1):
        if not pipei([57,50,89],im_pixel[x1,y],19):
            break
    x1-=1
    #左边缘x,y 右边缘 x1,y
    piece_w=x1-x
    piece_x= int((x+x1)/2)
    piece_y = y
    #棋子ok
    print('qizi',piece_x,piece_y)
    
    #269.156
    if piece_x>w/2: #棋子右半边
        xs=10
        x_m=1
    else:
        xs=w-10#棋子左半边
        x_m=-1
    ys=int(piece_y-abs(piece_x-xs)/269*156)
    bj_ys=list(im_pixel[xs,ys])
    print(xs,ys,bj_ys)
    #xs,ys 开始扫描颜色不同点
    for x in range(xs,piece_x,x_m):
        y=int(piece_y-abs(piece_x-x)/269*156)
        if not pipei(im_pixel[x,y],bj_ys,15):
            print(im_pixel[x,y])
            break 
    print(x,y,x_m)
    #get x,y
    bj_ys=list(im_pixel[10,y])
    wuxiao=x+274*x_m
    for x1 in range(x+274*x_m,x,-x_m):
        if x>wuxiao>x1 or x<wuxiao<x1:
            continue
        
        if not pipei(im_pixel[x,y],bj_ys,15):
            if pipei([60,70,70],im_pixel[x,y],20):
                wuxiao=x-x_m*piece_w
                continue
            break
    #get x1,y
    print(x1,y)
    x=(x+x1)/2
    xcha=abs(x-piece_x)
    return xcha


def check_screenshot():
    '''
    检查获取截图的方式
    '''
    global screenshot_way
    if os.path.isfile('autojump.png'):
        os.remove('autojump.png')
    if (screenshot_way < 0):
        print('暂不支持当前设备')
        sys.exit()
    pull_screenshot()
    try:
        Image.open('./autojump.png').load()
        print('采用方式 {} 获取截图'.format(screenshot_way))
    except Exception:
        screenshot_way -= 1
        check_screenshot()


def yes_or_no(prompt, true_value='y', false_value='n', default=True):
    default_value = true_value if default else false_value
    prompt = '%s %s/%s [%s]: ' % (prompt, true_value, false_value, default_value)
    i = input(prompt)
    if not i:
        return default
    while True:
        if i == true_value:
            return True
        elif i == false_value:
            return False
        prompt = 'Please input %s or %s: ' % (true_value, false_value)
        i = input(prompt)


def main():
    '''
    主函数
    '''
    op = yes_or_no('请确保手机打开了 ADB 并连接了电脑，然后打开跳一跳并【开始游戏】后再用本程序，确定开始？')
    if not op:
        print('bye')
        return
    print('程序版本号：{}'.format(VERSION))
    debug.dump_device_info()
    check_screenshot()

    i, next_rest, next_rest_time = 0, random.randrange(3, 10), random.randrange(5, 10)
    get_magicnumber()
    while True:
        pull_screenshot()
        im = Image.open('./autojump.png')
        # 获取棋子和 board 的位置
        xcha = find_piece_and_board(im)
        ts = int(time.time())
        print(ts, xcha)
        set_button_position(im)
        jump(xcha)
        if debug_switch:
            #debug.save_debug_screenshot(ts, im, piece_x, piece_y, board_x, board_y)
            debug.backup_screenshot(ts)
        i += 1
        if i == next_rest:
            print('已经连续打了 {} 下，休息 {}s'.format(i, next_rest_time))
            for j in range(next_rest_time):
                sys.stdout.write('\r程序将在 {}s 后继续'.format(next_rest_time - j))
                sys.stdout.flush()
                time.sleep(1)
            print('\n继续')
            i, next_rest, next_rest_time = 0, random.randrange(30, 100), random.randrange(10, 60)
        time.sleep(random.uniform(0.9, 1.2))   # 为了保证截图的时候应落稳了，多延迟一会儿，随机值防 ban


if __name__ == '__main__':
    main()
