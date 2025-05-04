import cv2
import numpy as np
import os

def compare_frames(frame1, frame2, method='ssim'):
    """比较两帧的相似度，默认使用结构相似性(SSIM)"""
    if frame1 is None or frame2 is None:
        return 0.0
    if frame1.shape != frame2.shape:
        frame2 = cv2.resize(frame2, (frame1.shape[1], frame1.shape[0]))
    if method == 'ssim':
        from skimage.metrics import structural_similarity as ssim
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        score, _ = ssim(gray1, gray2, full=True)
        return score
    else:
        # fallback: 均方误差
        mse = np.mean((frame1.astype("float") - frame2.astype("float")) ** 2)
        return 1.0 / (1.0 + mse)

def validate_video(output_path, golden_path, threshold=0.95, max_frames=300):
    """与黄金样本逐帧比对，返回整体相似度是否达标"""
    golden = cv2.VideoCapture(golden_path)
    test = cv2.VideoCapture(output_path)
    frame_idx = 0
    while True:
        golden_ret, golden_frame = golden.read()
        test_ret, test_frame = test.read()
        if not golden_ret or not test_ret or frame_idx >= max_frames:
            break
        sim = compare_frames(golden_frame, test_frame)
        assert sim > threshold, f"帧{frame_idx}相似度过低: {sim:.3f} < {threshold}"
        frame_idx += 1
    golden.release()
    test.release()
    return True

def batch_validate_videos(test_dir, golden_dir, threshold=0.95):
    """批量比对 test_dir 下所有视频与 golden_dir 下同名黄金样本"""
    for fname in os.listdir(test_dir):
        if not fname.lower().endswith(('.mp4', '.avi', '.mov')):
            continue
        test_path = os.path.join(test_dir, fname)
        golden_path = os.path.join(golden_dir, fname)
        if not os.path.exists(golden_path):
            print(f"黄金样本缺失: {fname}")
            continue
        print(f"比对: {fname}")
        validate_video(test_path, golden_path, threshold=threshold) 