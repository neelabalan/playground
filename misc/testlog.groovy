class LogUtil {
    static def log(String message) {
        def stackElement = new Exception().stackTrace[3]
        def lineNumber = stackElement.lineNumber
        def methodName = stackElement.methodName
        def timestamp = new Date().format("yyyy-MM-dd HH:mm:ss.SSS")
        println "${timestamp} [${methodName}:${lineNumber}] - ${message}"
    }
}

def someFunction() {
    LogUtil.log("this is from someFunction")
}


class Demo {
    static void sayHello() {
        LogUtil.log("from sayHello")
    }

}

someFunction()
Demo demoInstance = new Demo()
demoInstance.sayHello()

/*
2025-01-21 12:05:24.637 [someFunction:23] - this is from someFunction
2025-01-21 12:05:24.661 [sayHello:29] - from sayHello
*/