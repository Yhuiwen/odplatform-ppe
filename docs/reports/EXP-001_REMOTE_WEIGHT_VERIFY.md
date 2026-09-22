# EXP-001 REMOTE WEIGHT VERIFY

> Date: 2026-09-22
>
> Final status: **READY**
>
> Scope: remote initialization-weight transfer verification only
>
> Training authorization: NOT GRANTED
>
> Training started: NO
>
> Dataset modified: NO
>
> Mapping modified: NO
>
> EXP-001 configuration modified: NO

## Transfer Result

The registered YOLO11n initialization checkpoint was transferred to the
selected AutoDL training environment without changing the local artifact.

| Item | Value |
| --- | --- |
| Local path | `models/pretrained/yolo11n.pt` |
| Remote path | `/root/autodl-tmp/models/pretrained/yolo11n.pt` |
| Transport | SCP over the existing AutoDL SSH connection |
| Remote destination before transfer | MISSING |
| Transfer result | PASS |

The remote destination was checked before transfer. No existing file was
overwritten.

## Integrity Verification

| Check | Local | Remote | Match |
| --- | --- | --- | --- |
| File exists | YES | YES | PASS |
| Size | `5,613,764` bytes | `5,613,764` bytes | PASS |
| SHA256 | `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1` | `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1` | PASS |

Remote path resolved by `realpath`:

```text
/root/autodl-tmp/models/pretrained/yolo11n.pt
```

SHA256 match result:

```text
PASS
```

## Repository Verification

| Check | Result |
| --- | --- |
| `python -m pytest` | `179 passed` |
| `python -m compileall .` | PASS |
| `git diff --check` | PASS |
| Charter diff | EMPTY |

## Safety Boundary

| Control | Result |
| --- | --- |
| Training started | NO |
| Dataset modified | NO |
| Mapping modified | NO |
| Dataset fingerprints modified | NO |
| EXP-001 canonical configuration modified | NO |
| Model execution performed | NO |
| Commit created | NO |
| Push performed | NO |

This verification does not grant training authorization. The remote weight is
an initialization asset only and remains Git-ignored.

## Final Result

```text
READY
```
