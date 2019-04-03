
[安装]


(1)选择geckodriver.mac或者geckodriver.ubuntu，不带后缀名复制进$PATH目录，例如
cp geckodriver.mac /usr/local/bin/geckodriver
(2)安装火狐
apt-get install firefox
(3)安装脚本环境
python3 setup.py



[命令行参数用法]


(1)基本参数
python3 like.py [IG用户] [IG密码] [代理地址:端口:用户:密码]
除脚本名称外，其他均为可不填。




(2)功能型参数
-ap, --allocate-proxy
------------------------------------------------------------------------
后台自动分配代理
【举例】python3 like.py minhaodeng -ap



-p, --pull [group1] [group2] ...
------------------------------------------------------------------------
基本参数只需填写IG用户名。脚本自动从后台获取最近登录成功过的密码，代理，任务（仅run.py支持）。
pull后面可以选跟1个或多个group参数，其值可以为version，tasks等。如果指定group，则pull按照group分组获得信息。
【举例1】python3 like.py minhaodeng -p
pull最近登录成功的密码，代理。
【举例2】python3 run.py minhaodeng -p version
pull最近登录成功的，使用在相同version的run.py脚本里的密码，代理，任务。
【举例3】python3 run.py minhaodeng 12345678 -p -t follow
虽然pull最近的密码，代理，任务，但密码"12345678"、任务"follow"已经在参数中给出，pull不会覆盖这些参数。



-t, --tasks task1 [task2] ...
------------------------------------------------------------------------
指定要跑的tasks。仅run.py支持。
以tasks文件夹中的任务定义文件名为参数，不加".py"后缀。
需至少指定1个任务文件。不设上限。
同一个文件中的任务，依次执行，可指定子任务的冷却时间；不同文件中的任务，相互排队。
【举例】python3 run.py minhaodeng -p -t follow like-asia
脚本将自动获取密码和代理（不分组），并且混合执行tasks/follow.py和tasks/like-asia.py中定义的任务



-rp, --retry-proxy
------------------------------------------------------------------------
在代理无法连接网络的时候，允许重试。如果不指定这个参数，在登录前，判断出代理无效的时候脚本将直接退出
如果指定这个参数，默认以命令行询问方式取得新代理。
可以和-ap一起用。如果指定-ap，那就后台重新分配代理。




(3)其他参数
-q, --query
------------------------------------------------------------------------
一旦遇到需要从命令行输入任何信息的情况，改为从数据库查询相应字段的最新值。
用于和前端配合。



-v, --version [string]
-n, --name [string]
-i, --instance [string]
------------------------------------------------------------------------
用于标记脚本。在命令行处指定的这些参数，会覆盖文件中env.config()里的声明。
三者都可以被--pull识别用以分组。


