WXSender-Python
===============

WXSender 是用 Python 实现的微信公众平台微信发送接口，可以模拟在网页上登录微信公众平台，给指定或者所有好友发送微信。

WXSender 目前只支持纯文本消息的发送，可以作为一个消息群发器的接口，信息的数量每日不受限制。

Usage
===============
测试用例已经合成到 WXSender 类中，只需要如下代码即可测试：
    wxs = WXSender()
    wxs.run_test("abc@abc.com","abc")

程序会抛出运行过程中的错误。

Update
===============
2013-07-22 20:01
None.

2013-08-22 14:01:45
微信版本更新，微信 web 登陆验证逻辑稍有小的变更，上一次的版本不可用，已经修复；这个版本可以正常使用了。  

Proposal
===============
有 bug 请联系我：http://weibo.com/daoluanxiaozi
