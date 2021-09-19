HostSurvey 是本人的另一款用 go 写的整合工具，
功能：
1.主机发现
2.端口扫描
3.web server banner 识别

需要用到pcap进行抓包判断，
如果搞不定pcap的话可以用 HostSurvey.exe.test 代替，将 .test 去掉就可以用了；
Linux平台请下载源码在 package main 下的程序入口文件改动后自行编译；