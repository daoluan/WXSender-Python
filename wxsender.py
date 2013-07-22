# coding: UTF-8
import urllib2,cookielib,re
import json
from hashlib import md5

'''
    author:     daoluan
    datetime:   2013-07-22
'''

class WXSender:
    '''
        登录->获取微信公众账号 fakeid->获取好友 fakeid->向所有好友群发送微信或者向指定好友发送微信
        其中 fakeid 是在网页版微信中用到的参数，可以看作是用户的标识
        
        `登录过程中，主要是记录 cookie，在之后的通信中都要往 HTTP header 中添加 cookie，否则微信会作「登陆超时」处理，微信后台应该
            是用此 cookie 来作 session 的；另，在返回的 json 中有 token 参数，也需要记录，具体作用还不明，但发现一个现象：当下
            修改 token 为其他值不影响操作，但隔一天使用前一天的 token 则无效
        `获取的好友 fakeid 全在返回页面的 json 中
        `聊天，用 fiddler 抓包，所以手上三件东西就可以聊天了：cookie，fromfakeid 和 tofakeid
        
        ================== 聊天 HTTP 包 ==================
        POST https://mp.weixin.qq.com/cgi-bin/singlesend?t=ajax-response&lang=zh_CN HTTP/1.1
        Host: mp.weixin.qq.com
        Connection: keep-alive
        Content-Length: 90
        Accept: */*
        Origin: https://mp.weixin.qq.com
        X-Requested-With: XMLHttpRequest
        User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31
        Content-Type: application/x-www-form-urlencoded; charset=UTF-8
        Referer: https://mp.weixin.qq.com/cgi-bin/singlemsgpage?token=XXXXXX&fromfakeid=XXXXXX&msgid=&source=&count=20&t=wxm-singlechat&lang=zh_CN
        ……
        Cookie: ……

        type=1&content=hello+world&error=false&imgcode=&tofakeid=XXXXXX&token=XXXXXX&ajax=1
        ================== 聊天 HTTP 包 ==================
    '''
    wx_cookie = ''      
    token = ''
    betalife_fakeid = ''    # 微信公众账号 fakeid
    friend_info = []        # 好友 fakeid
    
#     def __init__(self):
#         pass
        
    def login(self,account,pwd):
        
        # 获取 cookie
        cookies = cookielib.LWPCookieJar()
        cookie_support= urllib2.HTTPCookieProcessor(cookies)
     
        # bulid a new opener
        opener = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)
        urllib2.install_opener(opener)
        
        m = md5()
        m.update(pwd)
        
        req = urllib2.Request(url = 'http://mp.weixin.qq.com/cgi-bin/login?lang=zh_CN',
                              data = ('username=' + 'daoluanxiaozi%40126.com' + 
                              '&pwd=' + m.hexdigest() + 
                              '&imgcode='
                              '&f=json'))
        
        respond = opener.open(req).read()
        
        print respond
        respond_json = json.loads(respond)
        
        if respond_json['ErrCode'] < 0:
            return False
        
        self.token = re.search(r'token=(\d+)', respond_json['ErrMsg']).group(1)
        
        for cookie in cookies:
            self.wx_cookie += cookie.name + '=' + cookie.value + ';'
        
#         print 'wx_cookie ',self.wx_cookie
#         print 'token ',self.token
        return True
    
    def get_fakeid(self):
        url = 'https://mp.weixin.qq.com/cgi-bin/userinfopage?t=wxm-setting&token=' + self.token + '&lang=zh_CN'
        req = urllib2.Request(url)
        req.add_header('cookie',self.wx_cookie)
        
        data = urllib2.urlopen(req,timeout = 4).read()
        
        m = re.search(r'fakeid = "(\d+)"',data,re.S | re.I)
        
        # group(0) == [fakeid = "123456789"]
        if m:
            self.betalife_fakeid = m.group(1)
            return True

        return False
    
    def get_friend_fakeid(self):
            # 获取 friend fakeid
        base_url = ('http://mp.weixin.qq.com/cgi-bin/contactmanagepage?t=wxm-friend&lang=zh_CN&pagesize=50' + 
                    '&type=0&groupid=0' + 
                    '&token=' + self.token + 
                    '&pageidx=')    # pageidx = ?
        
        # 这里可以根据微信好友的数量调整，由 base_url 可知一页可以显示 pagesize = 50 人，看实际情况吧。
        for page_idx in xrange(0,1000):
        
            url = base_url + str(page_idx)
            req = urllib2.Request(url)
            req.add_header('cookie',self.wx_cookie)
            data = urllib2.urlopen(req).read()
        
            match_res = re.search(r'<script id="json-friendList" type="json/text">(.*?)</script>',data,re.S)
        
            temp = json.loads(match_res.group(1))
            if temp == []:
                break        
            
            self.friend_info += temp
        print self.friend_info
        
    def group_sender(self,msg = None):

        if self.wx_cookie == '' | self.token == '' | self.betalife_fakeid == ''| self.friend_info == []:
            return False
        
        '''
        fakeId nickName groupId remarkName
        '''
        if msg is None:
            msg = 'Hello World.'
            
        url = 'https://mp.weixin.qq.com/cgi-bin/singlesend?t=ajax-response&lang=zh_CN'
        post_data = ('type=1&content=' + msg + '&error=false&imgcode='
                     '&token=' + self.token +
                     '&ajax=1&tofakeid=')   # fakeid = ?
        
        fromfakeid = self.betalife_fakeid
    
        for friend in self.friend_info:
            temp = (post_data + friend[u'fakeId']).encode('utf-8')
            
            req = urllib2.Request(url,temp)
            req.add_header('cookie',self.wx_cookie)
            
            # 添加 HTTP header 里的 referer 欺骗腾讯服务器。如果没有此 HTTP header，将得到登录超时的错误。
            req.add_header('referer', ('https://mp.weixin.qq.com/cgi-bin/singlemsgpage?'
                                   'token=' + self.token +
                                   '&fromfakeid=' + fromfakeid + 
                                   '&msgid=&source=&count=20&t=wxm-singlechat&lang=zh_CN'))
            data = urllib2.urlopen(req,data = '',timeout = 4).read()    # just ignore the return
            
        return True
            
    def run_test(self):
        # 登录，需要提供正确的账号密码
        self.login('123@abc.io', 'abcdef')
        
        # 获取微信公众账号 fakeid
        self.get_fakeid()
        
        # 获取微信好友的所有 fakeid，保存再 self.friend_info 中
        self.get_friend_fakeid()
        
        # 群发接口：目前只能发送文本信息
        self.group_sender()
        
if __name__ == '__main__':
    wxs = WXSender()
    wxs.run_test()
    
