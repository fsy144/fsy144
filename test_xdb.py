"""
测试 ip2region.xdb 文件是否能正常加载和查询
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ip2region.searcher import new_with_buffer
from ip2region.util import IPv4, IPv6, load_content_from_file

XDB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ip2region.xdb')

def test_xdb():
    print("=" * 60)
    print("ip2region.xdb 文件测试")
    print("=" * 60)
    
    # 1. 检查文件是否存在
    if not os.path.exists(XDB_PATH):
        print(f"❌ 错误：文件不存在 - {XDB_PATH}")
        return False
    
    file_size = os.path.getsize(XDB_PATH)
    print(f"📄 文件路径: {XDB_PATH}")
    print(f"📦 文件大小: {file_size:,} 字节 ({file_size/1024/1024:.2f} MB)")
    
    # 2. 尝试加载文件
    print("\n" + "-" * 60)
    print("尝试加载 xdb 文件...")
    try:
        c_buffer = load_content_from_file(XDB_PATH)
        print(f"✅ 文件加载成功，缓冲区大小: {len(c_buffer):,} 字节")
    except Exception as e:
        print(f"❌ 文件加载失败: {e}")
        return False
    
    # 3. 尝试创建搜索器（IPv4）
    print("\n" + "-" * 60)
    print("尝试创建 IPv4 搜索器...")
    try:
        searcher = new_with_buffer(IPv4, c_buffer)
        print("✅ IPv4 搜索器创建成功")
    except Exception as e:
        print(f"❌ IPv4 搜索器创建失败: {e}")
        searcher = None
    
    # 4. 测试 IPv4 查询
    if searcher:
        print("\n" + "-" * 60)
        print("测试 IPv4 查询...")
        test_ips = [
            "8.8.8.8",        # 美国 - Google DNS
            "114.114.114.114", # 中国 - 114DNS
            "223.5.5.5",      # 中国 - 阿里DNS
            "1.1.1.1",        # 美国 - Cloudflare
            "127.0.0.1",      # 本地回环
            "192.168.1.1",    # 内网
            "106.55.254.60",
            "188.253.124.94",
        ]
        
        for ip in test_ips:
            try:
                region = searcher.search(ip)
                print(f"  {ip:20s} -> {region}")
            except Exception as e:
                print(f"  {ip:20s} -> ❌ 查询失败: {e}")
    
    # 5. 尝试创建搜索器（IPv6）
    print("\n" + "-" * 60)
    print("尝试创建 IPv6 搜索器...")
    try:
        searcher6 = new_with_buffer(IPv6, c_buffer)
        print("✅ IPv6 搜索器创建成功")
        
        # 测试 IPv6 查询
        print("\n测试 IPv6 查询...")
        test_ipv6 = [
            "2001:4860:4860::8888",  # Google DNS
            "2400:3200::1",          # 阿里DNS
            "2408:8000::1",          # 中国电信
            "::1",                   # 本地回环
        ]
        
        for ip in test_ipv6:
            try:
                region = searcher6.search(ip)
                print(f"  {ip:40s} -> {region}")
            except Exception as e:
                print(f"  {ip:40s} -> ❌ 查询失败: {e}")
                
    except Exception as e:
        print(f"❌ IPv6 搜索器创建失败: {e}")
        print(f"   (这可能意味着该 xdb 文件只包含 IPv4 数据)")
    
    # 6. 分析返回格式
    print("\n" + "-" * 60)
    print("返回格式分析:")
    if searcher:
        try:
            region = searcher.search("42.84.233.94")
            parts = region.split('|')
            print(f"  原始返回: {region}")
            print(f"  分段数量: {len(parts)}")
            print(f"  各段内容:")
            labels = ["国家/地区", "区域/省份", "城市", "ISP", "运营商"]
            for i, part in enumerate(parts):
                label = labels[i] if i < len(labels) else f"段{i}"
                print(f"    {label}: {part}")
            
            # 检查是否符合代码中的预期格式
            print(f"\n  代码预期格式: 国家|省份|城市|ISP (4段)")
            print(f"  实际格式段数: {len(parts)} 段")
            if len(parts) >= 1:
                print(f"  国家字段: '{parts[0]}'")
                if parts[0] == '中国':
                    print(f"  ✅ 国家字段为'中国'，与代码 is_china_ip 判断一致")
                else:
                    print(f"  ⚠️  国家字段不是'中国'，代码中 country == '中国' 的判断可能不生效")
        except Exception as e:
            print(f"  ❌ 无法分析: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    return True

if __name__ == '__main__':
    test_xdb()
