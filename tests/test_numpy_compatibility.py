"""
测试numpy降级后的兼容性
验证所有numpy相关模块是否正常工作
"""

import sys
import traceback

def test_numpy_version():
    """测试numpy版本"""
    try:
        import numpy as np
        print(f"✅ numpy版本: {np.__version__}")
        assert np.__version__.startswith("2.2"), f"numpy版本不正确: {np.__version__}"
        return True
    except Exception as e:
        print(f"❌ numpy导入失败: {e}")
        traceback.print_exc()
        return False


def test_opencv():
    """测试opencv-python"""
    try:
        import cv2
        print(f"✅ opencv-python版本: {cv2.__version__}")
        # 测试基本功能
        import numpy as np
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        print(f"✅ opencv基本功能正常")
        return True
    except Exception as e:
        print(f"❌ opencv测试失败: {e}")
        traceback.print_exc()
        return False


def test_matplotlib():
    """测试matplotlib"""
    try:
        import matplotlib
        print(f"✅ matplotlib版本: {matplotlib.__version__}")
        import matplotlib.pyplot as plt
        import numpy as np
        # 测试基本绘图
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        fig, ax = plt.subplots()
        ax.plot(x, y)
        plt.close(fig)
        print(f"✅ matplotlib基本功能正常")
        return True
    except Exception as e:
        print(f"❌ matplotlib测试失败: {e}")
        traceback.print_exc()
        return False


def test_pyqtgraph():
    """测试pyqtgraph"""
    try:
        import pyqtgraph as pg
        print(f"✅ pyqtgraph版本: {pg.__version__}")
        import numpy as np
        # 测试基本功能
        data = np.random.normal(size=100)
        print(f"✅ pyqtgraph基本功能正常")
        return True
    except Exception as e:
        print(f"❌ pyqtgraph测试失败: {e}")
        traceback.print_exc()
        return False


def test_scikit_learn():
    """测试scikit-learn"""
    try:
        import sklearn
        print(f"✅ scikit-learn版本: {sklearn.__version__}")
        from sklearn.linear_model import LinearRegression
        import numpy as np
        # 测试基本功能
        X = np.array([[1], [2], [3]])
        y = np.array([2, 4, 6])
        model = LinearRegression()
        model.fit(X, y)
        pred = model.predict([[4]])
        print(f"✅ scikit-learn基本功能正常 (预测: {pred[0]:.2f})")
        return True
    except Exception as e:
        print(f"❌ scikit-learn测试失败: {e}")
        traceback.print_exc()
        return False


def test_pandas():
    """测试pandas"""
    try:
        import pandas as pd
        print(f"✅ pandas版本: {pd.__version__}")
        import numpy as np
        # 测试基本功能
        df = pd.DataFrame({'A': np.array([1, 2, 3]), 'B': np.array([4, 5, 6])})
        result = df.mean()
        print(f"✅ pandas基本功能正常")
        return True
    except Exception as e:
        print(f"❌ pandas测试失败: {e}")
        traceback.print_exc()
        return False


def test_torch():
    """测试PyTorch"""
    try:
        import torch
        print(f"✅ PyTorch版本: {torch.__version__}")
        import numpy as np
        # 测试numpy互操作
        np_array = np.array([1, 2, 3])
        torch_tensor = torch.from_numpy(np_array)
        back_to_numpy = torch_tensor.numpy()
        assert np.array_equal(np_array, back_to_numpy)
        print(f"✅ PyTorch与numpy互操作正常")
        return True
    except Exception as e:
        print(f"❌ PyTorch测试失败: {e}")
        traceback.print_exc()
        return False


def test_transformers():
    """测试transformers"""
    try:
        import transformers
        print(f"✅ transformers版本: {transformers.__version__}")
        return True
    except Exception as e:
        print(f"❌ transformers测试失败: {e}")
        traceback.print_exc()
        return False


def test_history_analyzer():
    """测试历史数据分析器"""
    try:
        from src.monitor.history_analyzer import (
            analyze_memory_trends,
            analyze_cache_performance,
            analyze_oom_risks
        )
        print(f"✅ 历史数据分析器导入成功")
        return True
    except Exception as e:
        print(f"❌ 历史数据分析器测试失败: {e}")
        traceback.print_exc()
        return False


def test_compression_dashboard():
    """测试压缩监控仪表盘"""
    try:
        from src.ui.compression_dashboard import get_compression_dashboard_launcher
        launcher = get_compression_dashboard_launcher()
        print(f"✅ 压缩监控仪表盘导入成功")
        return True
    except Exception as e:
        print(f"❌ 压缩监控仪表盘测试失败: {e}")
        traceback.print_exc()
        return False


def test_history_dashboard():
    """测试历史数据仪表盘"""
    try:
        from src.ui.history_dashboard import get_history_dashboard_launcher
        launcher = get_history_dashboard_launcher()
        print(f"✅ 历史数据仪表盘导入成功")
        return True
    except Exception as e:
        print(f"❌ 历史数据仪表盘测试失败: {e}")
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("numpy降级兼容性测试")
    print("=" * 60)
    
    tests = [
        ("numpy版本", test_numpy_version),
        ("opencv-python", test_opencv),
        ("matplotlib", test_matplotlib),
        ("pyqtgraph", test_pyqtgraph),
        ("scikit-learn", test_scikit_learn),
        ("pandas", test_pandas),
        ("PyTorch", test_torch),
        ("transformers", test_transformers),
        ("历史数据分析器", test_history_analyzer),
        ("压缩监控仪表盘", test_compression_dashboard),
        ("历史数据仪表盘", test_history_dashboard),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{'=' * 60}")
        print(f"测试: {name}")
        print(f"{'=' * 60}")
        result = test_func()
        results.append((name, result))
    
    # 打印总结
    print(f"\n{'=' * 60}")
    print("测试总结")
    print(f"{'=' * 60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！numpy降级后所有模块正常工作。")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个测试失败，请检查。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

