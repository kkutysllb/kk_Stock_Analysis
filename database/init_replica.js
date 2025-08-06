// MongoDB副本集初始化脚本
// 在mongo1容器中执行此脚本来初始化副本集

try {
    print("开始初始化MongoDB副本集...");
    
    // 切换到admin数据库
    db = db.getSiblingDB('admin');
    
    // 使用管理员权限连接
    db.auth('root', 'example');
    
    // 初始化副本集配置
    var config = {
        "_id": "rs0",
        "version": 1,
        "members": [
            {
                "_id": 0,
                "host": "mongo1:27017",
                "priority": 3  // 主节点优先级最高
            },
            {
                "_id": 1,
                "host": "mongo2:27017",
                "priority": 2  // 副本节点
            },
            {
                "_id": 2,
                "host": "mongo3:27017", 
                "priority": 1  // 副本节点
            }
        ]
    };
    
    // 初始化副本集
    var result = rs.initiate(config);
    print("副本集初始化结果:");
    printjson(result);
    
    if (result.ok === 1) {
        print("✅ 副本集初始化成功！");
        
        // 等待副本集状态稳定
        print("等待副本集状态稳定...");
        sleep(10000);  // 等待10秒
        
        // 检查副本集状态
        var status = rs.status();
        print("副本集状态:");
        printjson(status);
        
        // 显示副本集成员信息
        print("\n📊 副本集成员状态:");
        status.members.forEach(function(member) {
            print("- " + member.name + ": " + member.stateStr + " (健康度: " + member.health + ")");
        });
        
        print("\n🎯 副本集配置完成！");
        print("主节点: " + status.members.find(m => m.stateStr === "PRIMARY").name);
        print("副本节点数: " + status.members.filter(m => m.stateStr === "SECONDARY").length);
        
    } else {
        print("❌ 副本集初始化失败:");
        printjson(result);
    }
    
} catch (error) {
    print("❌ 副本集初始化过程中发生错误:");
    print(error);
    
    // 尝试获取当前状态信息
    try {
        var currentStatus = rs.status();
        print("当前副本集状态:");
        printjson(currentStatus);
    } catch (statusError) {
        print("无法获取副本集状态:", statusError);
    }
}