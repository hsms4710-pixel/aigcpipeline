# 流水线门禁经验库（自动沉淀）

> 门禁 FAIL 时自动追加；人工修正后可在此补充规避建议。

## 2026-08-14T23:02:36  |  stage=s2_rig  |  job=job_test_gate
- FAIL - F2 重复骨名: ['leftElbow', 'leftKnee', 'rightElbow', 'rightKnee']
- FAIL - F4 槽位引用不存在的骨骼: ['FaceWarp', 'MouthWarp']（StretchyStudio Warp 骨未导出）
- FAIL - F5 无 IK 约束（脚会滑、膝肘不自然）

## 2026-08-14T23:05:30  |  stage=s2_rig  |  job=job_e2a8fd07
- FAIL - F2 重复骨名: ['leftElbow', 'leftKnee', 'rightElbow', 'rightKnee']
- FAIL - F4 槽位引用不存在的骨骼: ['EyeLWarp', 'EyeRWarp', 'EyebrowLWarp', 'EyebrowRWarp', 'FaceWarp', 'HairBackWarp', 'HairFrontWarp', 'MouthWarp', 'NeckWarp', 'TopWearWarp']（StretchyStudio Warp 骨未导出）
- FAIL - F5 无 IK 约束（脚会滑、膝肘不自然）

## 2026-08-15T02:51:16  |  stage=s3_animate  |  job=job_f91e9c51
- FAIL - F1 缺必需 clip: attack
- FAIL - F1 缺必需 clip: hurt
- FAIL - F2 clip 时长无效: idle
- FAIL - F3 空动画: idle 无骨骼轨道
- FAIL - F2 clip 时长无效: walk
- FAIL - F3 空动画: walk 无骨骼轨道

