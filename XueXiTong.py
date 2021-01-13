#-*-coding:utf-8-*-
import base64
import json
import os
import re
import time
from typing import Union, Tuple, List, Optional, Any, Dict

import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3858.400 QQBrowser/10.7.4309.400"
}
class XueXiTong:
    def __init__(self, username, password):
        self.username = username
        self.password = base64.b64encode(password.encode()).decode()
        self.login()

    def login(self):
        data = {
            "fid": "-1",
            "uname": self.username,
            "password": self.password,
            "refer": "http%253A%252F%252Fi.chaoxing.com",
            "t": "true",
            "forbidotherlogin": "0"
        }
        r = requests.post("http://passport2.chaoxing.com/fanyalogin", data=data)
        if '"status":true' in r.text:
            self.cookies = r.cookies
            print("登录成功!")
        else:
            raise Exception("登录失败!")

    def current_progress(self):
        url = "https://mooc1-1.chaoxing.com/moocAnalysis/progressStatisticData?courseId=203986614&classId=30498035&userId=68369903&debug=false&rank=0&pageSize=30&pageNum=1&ut=s&cpi=68369903&preRank=&preJobFinshCount=&preStuCount=&statisticSystem=0&openc=86914c99ca9916e22dd53720917d6e9a"
        r = requests.get(url, headers=headers, cookies=self.cookies)
        study_num = re.findall('章节学习次数：(\d+)&', r.text)[0]
        return study_num

    def add_chapter_view(self):
        url = "https://fystat-ans.chaoxing.com/log/setlog?personid=68369903&courseId=203986614&classId=30498035&encode=b1e16a51f185b4e6c6f0e2618ce93402&chapterId=151414454&_=1608971823951"
        r = requests.get(url, headers=headers, cookies=self.cookies)
        if r.text == "'success'":
            print("[章节当前学习次数:%s] 章节访问次数+1" % self.current_progress())
        else:
            print("发生错误！")

class YunPan(XueXiTong):
    def __init__(self, account, password):
        super().__init__(account, password)

    def _filename_to_id_puid(self, filename: str) -> Tuple[str, str]:
        for file in self._file_catalog():
            if file['name'] == filename:
                return file['id'], str(file['puid'])

    # 文件目录
    def _file_catalog(self) -> List[Dict]:
        r = requests.post(
            'http://pan-yz.chaoxing.com/opt/listres?puid=0&shareid=0&parentId=258248751245365248&page=1&size=50&enc=6df5aa1998340392984482e3d7f00ed3',
            cookies=self.cookies)
        d = json.loads(r.text)
        data = d['list']
        return data

    # 获取公开下载链接
    def _file_share(self, id):
        """获取公开下载链接

        :param id: 文件的ID号
        :return: 文件的下载链接
        """
        form_data = {
            "resids": "%s" % id,
            "type": "SHARE_NORMAL",
            "vt": "VT_FOREVER"
        }
        r = requests.post('http://pan-yz.chaoxing.com/share/create', data=form_data, cookies=self.cookies)
        data = json.loads(r.text)
        download_url = data['data']['weburl']
        return download_url

    # 上传文件
    def upload_file(self, filedress: str, auto_share: bool = False) -> Optional[Tuple[Union[bytes, str], int, Any, int]]:
        r = requests.get('http://pan-yz.chaoxing.com/opt/getLimitFlow?_={}'.format(time.time()), cookies=self.cookies)
        file_maxsize = int(re.findall('"filesize":(.*?)}', r.text)[0])
        print(file_maxsize)
        file_size = os.path.getsize(filedress)
        filename = os.path.basename(filedress)
        if file_size <= file_maxsize:
            files = {
                "folderId": (None, "258248751245365248"),
                # "puid": (None,"0",),
                # "id": (None,"WU_FILE_1"),
                # "name": (None,"%s"%filename),
                # "type": (None,"image/jpeg"),
                'file': (filename, open(filedress, 'rb'))
            }
            print('[上传中] 文件名：%s 大小：%sM 预计耗时：%ss' % (
            filename, round(file_size / 1024 ** 2, 2), round((file_size / 1024 ** 2) / 6, 2)))
            r = requests.post('http://pan-yz.chaoxing.com/opt/upload', files=files, cookies=self.cookies)
            upload_time = int(time.time() * 1000)
            if '上传成功' in r.text:
                if auto_share == False:
                    print('[上传成功] 文件名：%s 大小：%sM' % (filename, round(file_size / 1024 ** 2, 2)))
                    return
                # 生成文件分享链接
                download_url = self._file_share(self._file_catalog()[0]['id'])
                return (filename, file_size, download_url, upload_time)
            return

    # 下载文件
    def download_file(self, filename: str) -> Union[bytes, None]:
        fileid, puid = self._filename_to_id_puid(filename)
        params = {
            "fleid": fileid,
            "puid": puid
        }
        r = requests.get("http://pan-yz.chaoxing.com/download/downloadfile", params=params, cookies=self.cookies,
                         headers=headers)
        if r.status_code == 200:
            return r.iter_content(chunk_size=1024*5)
        else:
            return

y = YunPan("用户名","密码")
print(y.upload_file("test.py"))
print(y.download_file("test.py"))
