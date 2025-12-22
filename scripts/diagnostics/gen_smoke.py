import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from src.core.real_ai_engine import RealAIEngine

def main():
    try:
        engine = RealAIEngine()
        ok = engine.load_model('zh')
        print('LOAD_OK', ok, 'DEVICE', engine.device)
        if not ok:
            print('FAIL: load_model returned False')
            return 2
        out = engine.generate('你是谁？请用中文一句话回答。', language='zh', max_tokens=16)
        print('GEN_LEN', len(out))
        print(out[:200].replace('\n',' '))
        engine.cleanup()
        if engine.device != 'cuda':
            print('WARN: device is not cuda, still pass as CPU fallback')
        return 0 if len(out.strip()) > 0 else 3
    except Exception as e:
        print('ERROR:', e)
        return 4

if __name__ == '__main__':
    sys.exit(main())

