# -*- coding: utf-8 -*-
"""
Created on Thu Oct 27 18:30:33 2022

@author: Yokohama National University, Kosaka Lab
"""


import copy
import random
import time
from qiskit.providers.jobstatus import JobStatus
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
 #グラフの描画のためのインポート
import sys
sys.path.append("..")
import matplotlib.pyplot as plt  #ここイランかも
import numpy as np
from exceptions.exceptions import RedCalibrationError, KosakaQRedcalibrationError
from KosakaQbackend import KosakaQbackend
from job.job_monitor import job_monitor

class Red_calibration():
    def __init__(self):
        self.mode = None
        self.job_num = 0
        self.job = []
        self.mode = []
        self.calibration = []
        self.backend = KosakaQbackend("rabi")
    
    def run(self, mode):  # 大輔が作ります
        """
        mode: Ey or E1E2 or all
        どの周りのスペクトルを取るか選べる。
        """
        # self.result = []  # Rabi_project20_E6EL06_area06_NV04_PLE_all_0.txtの内容が入ったlistを返します。
        # self.power = []  #周波数 vs.laser_power
        self.job.append(self.backend.run(mode))
        self.job_num += 1  # 発行したjobの数
        self.mode.append(mode)
        self.flag.append({})  # 各種Flag
        self.flag[-1]["get_result"] = False
        self.flag[-1]["calibration"] = False
        self.flag[-1]["fitting"] = False
        return self.job[-1]  # result[0]=frequencyのlist, result[1]=count（縦軸), result[2] = エラーバーのlist
    

    def jobs(self):
        if self.job_num == 0:
            print("There is no job.")
        else:
            for i in range(self.job_num):
                if self.flag[i]["get_result"] == False:
                    print("job",i+1,"... ","mode: ",self.mode[i], " get_result: not yet")
                else:
                    print("job",i+1,"... ","mode: ",self.mode[i], " get_result: done")
             

    # author: Goto Kyosuke
    def get_result(self, job_num = 0):  # job_num = 0にすることで、使うとき job_num-1 = -1 となり、最新のが使える。
        if job_num > self.job_num or job_num < 0 or not( type(job_num) == int ):
            raise KosakaQRedcalibrationError
        
        if self.flag[-1]["get_result"] == True:
            print("Already executed")
        
        # job_status確認して表示
        nowstatus = self.job[job_num].status()
        print(nowstatus.value)
        
        # status:queuedだったら、何番目か表示して、このまま待つか聞いて、待つようだったらjob monitor表示
        if nowstatus == JobStatus.QUEUED:
            print("You're job number is ",self.job[job_num].queue_position())
            ans = input("Do you wait? y/n:")
            if ans == "y" or "yes":
                job_monitor()
            else:
                raise KosakaQRedcalibrationError
                
        while (not (self.job[job_num].status() == JobStatus.DONE)):
            if nowstatus == JobStatus.DONE: # status:doneだったら/なったら、result取ってくる。
                result = self.job[job_num].result() #resultはResultクラスのインスタンス
            time.sleep(random.randrange(8, 12, 1))
        
        self.flag[job_num-1]["get_result"] = True
        
        return result.data()
        
        # result[job_num-1][0]=frequencyのlist, result[job_num-1][1]=count（縦軸), result[job_num-1][2] = エラーバーのlist


    # author: Mori Yugo
    def draw(self, fitting=False, error=0, Ey=False, E1E2=False, save=False, job_num = 0):
        """
        This function draws photoluminescence excitation (PLE).
        
        fitting: True or false
           フィッティングするか選ぶ
        error: 0, 1, 2 or 3
           1.範囲をエラーバーとするグラフを表示
           2.標準偏差をエラーバーとするグラフを表示
           3.標準誤差をエラーバーとするグラフを表示
        Ey: True or false
           Eyの中心値を表示するか選ぶ
        E1E2: True or false
           E1E2の中心値を表示するか選ぶ
        save: True or false
           Ey, E1E2を保存するか選べる
        """
        if job_num > self.job_num or job_num < 0 or not( type(job_num) == int ):   #get resultにデータがあるか
            raise KosakaQRedcalibrationError
        
        if self.mode == None:   # runをまだ実行してなかったら(self.mode == None)、エラーを返す。（これは最初でやるべき？）
            raise KosakaQRedcalibrationError("Run function is not done.")
        
        if fitting == True:   # optionでfittingするか選べる ← fitingのlistには_make_fittingメソッドを使って下さい。
            self._make_fitting(job_num)
        
        fre_y = copy.deepcopy[self.result[job_num - 1][0]]  # 縦軸の値  # これいらんかも（しかし、これ消すとエラー出る）
        cou_x = copy.deepcopy[self.result[job_num - 1][1]]  # 横軸の値
        # optionでエラーバーいれるか選べる。
        # 参考文献: https://dreamer-uma.com/errorbar-python/
        fre_y_mean = np.array(fre_y.mean())   # 各点を平均値とする
        if error == 1:   # 範囲をエラーバーとしたグラフ
            fre_yerr_scope = np.array(fre_y.max() - fre_y.min())   #データの範囲
            fig, ax = plt.subplots()
            ax.plot(cou_x, fre_y, marker='o')
            ax.errorbar(cou_x, fre_y_mean, fre_yerr=fre_yerr_scope, capsize=3, fmt='o', ecolor='k', ms=7, mfc='None', mec='k')
            ax.set_title('photoluminescence excitation (PLE) - error bar: scope')
        elif error == 2:   # 標準偏差をエラーバーとしたグラフ
            fre_yerr_sd = np.array(fre_y.std())   #標準偏差
            fig, ax = plt.subplots()
            ax.plot(cou_x, fre_y, marker='o')
            ax.errorbar(cou_x, fre_y_mean, fre_yerr=fre_yerr_sd, capsize=3, fmt='o', ecolor='k', ms=7, mfc='None', mec='k')
            ax.set_title('photoluminescence excitation (PLE) - error bar: SD')
        elif error == 3:   # 標準誤差をエラーバーとしたグラフ
            fre_yerr_se = np.array(fre_y.std() / np.sqrt(len(fre_y)))   #標準偏差
            fig, ax = plt.subplots()
            ax.plot(cou_x, fre_y, marker='o')
            ax.errorbar(cou_x, fre_y_mean, fre_yerr=fre_yerr_se, capsize=3, fmt='o', ecolor='k', ms=7, mfc='None', mec='k')
            ax.set_title('photoluminescence excitation (PLE) - error bar: SE')
        ax.set_xlabel('count')
        ax.set_xlabel('frequency')
        plt.show()
        
        if Ey == True:   # optionでE1E2,Eyの中心値を表示するか選べる。 ← 中心値にはcalibrationメソッドを使ってください。
            self.calibration(job_num)
        if E1E2 == True:
            self.calibration(job_num)
        
        if save == True:   # optionで保存するか選べる。(保存とは何の保存を意味しているのか？)
            f = open("calibration.txt")
            f.write("calibration")
            f.write(str(self.calibration[job_num-1]))
            f.close()
        
        # その他、optionを入れる。optionは引数にするが、あくまでoptionなので、選ばなくても良いようにする。
    
    
    # author: Mori Yugo
    def laser_draw(self, fitting=False, Ey=False, E1E2=False, save=False, job_num = 0):
        # optionでfittingするか選べる ← fitingのlistはこちらは簡単だと思うので、自分で作って下さい。
        # optionで保存するか選べる。
        # その他、optionを入れる。optionは引数にするが、あくまでoptionなので、選ばなくても良いようにする。
        if self.mode == None:   # runをまだ実行してなかったら(self.mode == None)、エラーを返す。（これは最初でやるべき？）
            raise KosakaQRedcalibrationError("Run function is not done.")
        pass

    # author: Honda Yuma
    def calibration(self, job_num = 0):  # E1E2とEyのキャリブレーション結果を返す ← E1E2は二つの頂点のちょうど中心を取る。Eyは_make_fittingのself.x0を返す。
        # runをまだ実行してなかったら(self.mode == None)、エラーを返す。
        # 結果は　self.calibration[job_num-1]に辞書で入れる。例）[{E1E2:470.0678453678},{E1E2:470.0034567, Ey:470.145678}]
        pass
    
    
    def save(self, job_num = 0):  # jsonにE1とExEy保存する。
        pass
    

    # author: Ebihara Syo
    def _make_fitting(self, job_num = 0):
        #E1,E2はエラーを返す
        #Eyについてのfitingのlistを返す（ローレンチアン）、x0とγをself.x0とself.gammaに代入
        #runをまだ実行してなかったら(self.mode == None)、エラーを返す。
        
        if self.mode == "E1":  # E1の場合
            raise KosakaQRedcalibrationError('E1です')
            
        elif self.mode == "E2":  # E2の場合
            raise KosakaQRedcalibrationError('E2です')
            
        elif self.mode == "Ey":  # Eyの場合
            fre_y = copy.deepcopy[self.result[job_num - 1][0]]  # 縦軸の値
            cou_x = copy.deepcopy[self.result[job_num - 1][1]]  # 横軸の値
            
            
            
            # Ey_frequencyはフィッティング後の縦軸の値
            Ey_frequency = 1
            return Ey_frequency
        
        elif self.mode == "All":  # 全体の場合
            return 0
        
