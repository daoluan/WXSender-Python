# coding: UTF-8
import urllib2,cookielib,re
import json
import hashlib

'''
    author:     daoluan
    datetime:   2013-07-22
    
    update:    2013-08-22
    update:    2013-08-28 这个版本也可以用
'''
def goodboy(funcname): print "%s finished." % funcname

class WXSender:
    
    '''
        登录->获取微信公众账号 fakeid->获取好友 fakeid->向所有好友群发送微信或者向指定好友发送微信
        其中 fakeid 是在网页版微信中用到的参数，可以看作是用户的标识
        
        `登录过程中，主要是记录 cookie，在之后的通信中都要往 HTTP header 中添加 cookie，否则微信会作「登陆超时」处理，微信后台应该
            是用此 cookie 来作 session 的；另，在返回的 json 中有 token 参数，也需要记录，具体作用还不明，但发现一个现象：当下
            修改 token 为其他值不影响操作，但隔一天使用前一天的 token 则无效
        `获取的好友 fakeid 全在返回页面的 json 中
        `聊天，用 fiddler 抓包，所以手上三件东西就可以聊天了：cookie，fromfakeid 和 tofakeid
    '''
    
    wx_cookie = ''      
    token = ''
    user_fakeid = ''    # 微信公众账号 fakeid
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
        
        pwd = hashlib.md5(pwd).hexdigest()
        req = urllib2.Request(url = 'https://mp.weixin.qq.com/cgi-bin/login?lang=zh_CN',
                              data = ('username=' + account + 
                              '&pwd=' + pwd + 
                              '&imgcode='
                              '&f=json'))
        
        req.add_header("x-requested-with", "XMLHttpRequest")
        req.add_header("referer", "https://mp.weixin.qq.com/cgi-bin/loginpage?t=wxm2-login&lang=zh_CN")
        respond = opener.open(req).read()
        
        respond_json = json.loads(respond)
        
        if respond_json['ErrCode'] < 0:
            raise Exception("Login error.")
        
        s = re.search(r'token=(\d+)', respond_json['ErrMsg'])
        
        if not s:
            raise Exception("Login error.")
        
        self.token = s.group(1)
        
        for cookie in cookies:
            self.wx_cookie += cookie.name + '=' + cookie.value + ';'
#         print 'wx_cookie ',self.wx_cookie
#         print 'token ',self.token
        
        goodboy(self.login.__name__)
        
    def get_fakeid(self):
        if not (self.wx_cookie and self.token):
            raise Exception("Cookies or token is missing.")
        
        url = 'https://mp.weixin.qq.com/cgi-bin/userinfopage?t=wxm-setting&token=' + self.token + '&lang=zh_CN'
        req = urllib2.Request(url)
        req.add_header('cookie',self.wx_cookie)
        
        data = urllib2.urlopen(req,timeout = 4).read()
        
        m = re.search(r'fakeid = "(\d+)"',data,re.S | re.I)
        
        # group(0) == [fakeid = "123456789"]
        if not m:
            raise Exception("Getting fakeid failed.")
        
        self.user_fakeid = m.group(1)
        
        goodboy(self.get_fakeid.__name__)
        
    def get_friend_fakeid(self):
        if not (self.wx_cookie and self.token and self.user_fakeid):
            raise Exception("Cookies,token or user_fakeid is missing.")
        
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
            
            m = re.search(r'friendsList : \({"contacts":(.*?)}\)\.contacts',data,re.S)
            m_json = json.loads(m.group(1))
            if not m_json:
                break  
            
            self.friend_info += m_json
#         print self.friend_info
        
    def group_sender(self,msg = "Hello World."):
        if not (self.wx_cookie and self.token and self.user_fakeid and self.friend_info):
            raise Exception("Cookies,token,user_fakeid or friend_info is missing.")
        
        '''
        fakeId nickName groupId remarkName
        '''
        url = 'https://mp.weixin.qq.com/cgi-bin/singlesend?t=ajax-response&lang=zh_CN'
        post_data = ('type=1&content=%s&error=false&imgcode='
             '&token=%s'
             '&ajax=1&tofakeid=') % (msg,self.token)   # fakeid = ?
             
        fromfakeid = self.user_fakeid
        
        for friend in self.friend_info:
            postdata = (post_data + friend["id"]).encode('utf-8')
            
            req = urllib2.Request(url,postdata)
            req.add_header('cookie',self.wx_cookie)
            
            # 添加 HTTP header 里的 referer 欺骗腾讯服务器。如果没有此 HTTP header，将得到登录超时的错误。
            req.add_header('referer', ('https://mp.weixin.qq.com/cgi-bin/singlemsgpage?'
                                   'token=%s&fromfakeid=%s'
                                   '&msgid=&source=&count=20&t=wxm-singlechat&lang=zh_CN') % (self.token,fromfakeid))
            
            # {"ret":"0", "msg":"ok"}
            res = urllib2.urlopen(req).read()
            res_json = json.loads(res)
            
            if res_json["ret"] != "0":
                # do something.
                pass
            
        goodboy(self.get_friend_fakeid.__name__)
            
    def run_test(self,account,pwd):
        # 登录，需要提供正确的账号密码
        self.login(account, pwd)
        
        # 获取微信公众账号 fakeid
        self.get_fakeid()
        
        # 获取微信好友的所有 fakeid，保存再 self.friend_info 中
        self.get_friend_fakeid()
        
        # 群发接口：目前只能发送文本信息
        self.group_sender("test")
        
if __name__ == '__main__':
    wxs = WXSender()
    wxs.run_test("abc@abc.com","abc")