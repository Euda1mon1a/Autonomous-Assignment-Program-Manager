# Codex Safe Prune Plan

- Timestamp: `2026-02-26 12:42:22 HST`
- Worktree root: `/Users/aaronmontgomery/.codex/worktrees`
- Base ref: `origin/main`
- Excluded IDs: `bad1`
- Mode: `plan-only`

## BLUF

- Worktrees scanned: `227`
- Prune-ready now: `103`
- Excluded by policy: `0`
- Blocked (dirty/unique): `124`

Safe prune set: `0120,054c,070f,0753,09f3,0c72,0db0,0dcf,0f9b,10c5,18d3,1ca3,2934,2983,2b26,2f83,3117,3196,323a,32cd,33fc,34cb,40d9,4111,4601,4933,4a03,5208,53de,5492,5536,55dd,5612,5636,5995,5afe,5e1a,6063,61e2,632e,63d4,64e8,6a5e,6e42,70ea,7148,7361,73dc,7446,7aca,7e7d,7ef7,7f10,8743,8750,879a,8a3f,8adc,8e59,913d,9204,9554,98ab,9ee8,a864,a930,a9fb,acd8,ace3,b8ad,ba3f,bc9b,bec3,c377,c40e,c684,c885,cae7,cd4a,cdd5,ce37,d5c1,d77b,da6c,dbf3,de23,de58,de7c,e4f3,e61e,e728,e7ba,e8d8,e91d,eb8c,ebc8,eef1,f023,fa48,fd74,fd75,fe31,feb9`

## Plan Table

| ID | Dirty | Unique | Decision | Reason |
|---|---:|---:|---|---|
| `003a` | 0 | 2 | `keep` | unique commits |
| `0120` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `01da` | 45 | 0 | `keep` | dirty worktree |
| `0235` | 0 | 2 | `keep` | unique commits |
| `041a` | 45 | 0 | `keep` | dirty worktree |
| `04bd` | 0 | 2 | `keep` | unique commits |
| `054c` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `060e` | 67 | 0 | `keep` | dirty worktree |
| `06bc` | 1 | 0 | `keep` | dirty worktree |
| `070f` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `0753` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `0808` | 47 | 0 | `keep` | dirty worktree |
| `0894` | 66 | 0 | `keep` | dirty worktree |
| `09f3` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `0a9d` | 45 | 0 | `keep` | dirty worktree |
| `0bd0` | 1 | 0 | `keep` | dirty worktree |
| `0c72` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `0d12` | 0 | 2 | `keep` | unique commits |
| `0db0` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `0dcf` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `0f9b` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `1031` | 0 | 2 | `keep` | unique commits |
| `1060` | 45 | 0 | `keep` | dirty worktree |
| `10c5` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `10e8` | 45 | 0 | `keep` | dirty worktree |
| `18d3` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `1a5c` | 18 | 2 | `keep` | dirty worktree |
| `1bf5` | 0 | 2 | `keep` | unique commits |
| `1ca3` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `1e2f` | 1 | 0 | `keep` | dirty worktree |
| `1ee9` | 66 | 0 | `keep` | dirty worktree |
| `20f0` | 67 | 0 | `keep` | dirty worktree |
| `2341` | 66 | 0 | `keep` | dirty worktree |
| `2785` | 45 | 0 | `keep` | dirty worktree |
| `28ce` | 7 | 0 | `keep` | dirty worktree |
| `28e1` | 0 | 2 | `keep` | unique commits |
| `2934` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `2983` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `2ab4` | 45 | 0 | `keep` | dirty worktree |
| `2b26` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `2cc9` | 45 | 0 | `keep` | dirty worktree |
| `2e02` | 1 | 0 | `keep` | dirty worktree |
| `2f83` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `2fda` | 45 | 0 | `keep` | dirty worktree |
| `3117` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `3196` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `31c9` | 0 | 2 | `keep` | unique commits |
| `323a` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `32cd` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `33fc` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `34cb` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `3531` | 2 | 0 | `keep` | dirty worktree |
| `35e8` | 0 | 2 | `keep` | unique commits |
| `3a26` | 2 | 0 | `keep` | dirty worktree |
| `3ad5` | 51 | 0 | `keep` | dirty worktree |
| `3ae3` | 1 | 0 | `keep` | dirty worktree |
| `3ae4` | 0 | 2 | `keep` | unique commits |
| `3c09` | 66 | 0 | `keep` | dirty worktree |
| `3e8e` | 4 | 0 | `keep` | dirty worktree |
| `40d9` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `4111` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `4601` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `4706` | 0 | 2 | `keep` | unique commits |
| `474f` | 66 | 0 | `keep` | dirty worktree |
| `4822` | 0 | 2 | `keep` | unique commits |
| `4933` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `4a03` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `4a80` | 68 | 0 | `keep` | dirty worktree |
| `4c11` | 1 | 0 | `keep` | dirty worktree |
| `4d09` | 45 | 0 | `keep` | dirty worktree |
| `4fad` | 45 | 0 | `keep` | dirty worktree |
| `4fb8` | 45 | 0 | `keep` | dirty worktree |
| `5177` | 1 | 0 | `keep` | dirty worktree |
| `5208` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `53de` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `544a` | 2 | 0 | `keep` | dirty worktree |
| `5488` | 45 | 0 | `keep` | dirty worktree |
| `5492` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `5536` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `55dd` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `5612` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `5636` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `5995` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `5afe` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `5d3b` | 45 | 0 | `keep` | dirty worktree |
| `5e1a` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `5f2b` | 45 | 0 | `keep` | dirty worktree |
| `604a` | 45 | 0 | `keep` | dirty worktree |
| `6063` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `61e2` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `61fc` | 0 | 2 | `keep` | unique commits |
| `632e` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `63d4` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `64e8` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `69e8` | 66 | 0 | `keep` | dirty worktree |
| `6a5e` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `6d2e` | 57 | 0 | `keep` | dirty worktree |
| `6e42` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `7091` | 0 | 2 | `keep` | unique commits |
| `70ea` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `7148` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `71c4` | 2 | 0 | `keep` | dirty worktree |
| `7361` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `73dc` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `7446` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `757a` | 1 | 0 | `keep` | dirty worktree |
| `77d0` | 3 | 0 | `keep` | dirty worktree |
| `7aca` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `7bf9` | 0 | 2 | `keep` | unique commits |
| `7c67` | 71 | 0 | `keep` | dirty worktree |
| `7cb3` | 68 | 0 | `keep` | dirty worktree |
| `7d86` | 0 | 2 | `keep` | unique commits |
| `7e7d` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `7ef7` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `7f10` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `83a7` | 66 | 0 | `keep` | dirty worktree |
| `8407` | 2 | 0 | `keep` | dirty worktree |
| `8743` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `8750` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `879a` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `879c` | 45 | 0 | `keep` | dirty worktree |
| `8a3f` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `8adc` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `8be5` | 45 | 0 | `keep` | dirty worktree |
| `8d37` | 45 | 0 | `keep` | dirty worktree |
| `8e2c` | 29 | 0 | `keep` | dirty worktree |
| `8e59` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `8f7f` | 2 | 0 | `keep` | dirty worktree |
| `90af` | 72 | 0 | `keep` | dirty worktree |
| `913d` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `9204` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `926a` | 0 | 2 | `keep` | unique commits |
| `9315` | 72 | 0 | `keep` | dirty worktree |
| `9554` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `98ab` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `98ed` | 45 | 0 | `keep` | dirty worktree |
| `998e` | 45 | 0 | `keep` | dirty worktree |
| `9ece` | 1 | 0 | `keep` | dirty worktree |
| `9ee8` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `9f55` | 67 | 0 | `keep` | dirty worktree |
| `9f7a` | 2 | 2 | `keep` | dirty worktree |
| `a02d` | 45 | 0 | `keep` | dirty worktree |
| `a30d` | 45 | 0 | `keep` | dirty worktree |
| `a38c` | 66 | 0 | `keep` | dirty worktree |
| `a3be` | 1 | 2 | `keep` | dirty worktree |
| `a864` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `a930` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `a9e9` | 45 | 0 | `keep` | dirty worktree |
| `a9fb` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `ab5a` | 72 | 0 | `keep` | dirty worktree |
| `ac1e` | 45 | 0 | `keep` | dirty worktree |
| `acd8` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `ace3` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `adc1` | 46 | 0 | `keep` | dirty worktree |
| `ae22` | 0 | 2 | `keep` | unique commits |
| `af1b` | 66 | 0 | `keep` | dirty worktree |
| `b105` | 26 | 0 | `keep` | dirty worktree |
| `b348` | 45 | 0 | `keep` | dirty worktree |
| `b39e` | 0 | 2 | `keep` | unique commits |
| `b54f` | 1 | 0 | `keep` | dirty worktree |
| `b564` | 66 | 0 | `keep` | dirty worktree |
| `b8ad` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `ba3f` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `bc9b` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `bd36` | 0 | 2 | `keep` | unique commits |
| `bd9f` | 45 | 0 | `keep` | dirty worktree |
| `bde2` | 0 | 2 | `keep` | unique commits |
| `bec3` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `bf0a` | 5 | 0 | `keep` | dirty worktree |
| `c0c6` | 2 | 0 | `keep` | dirty worktree |
| `c2e0` | 47 | 0 | `keep` | dirty worktree |
| `c335` | 0 | 2 | `keep` | unique commits |
| `c377` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `c40e` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `c684` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `c775` | 4 | 2 | `keep` | dirty worktree |
| `c845` | 0 | 2 | `keep` | unique commits |
| `c885` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `c94f` | 2 | 0 | `keep` | dirty worktree |
| `cae7` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `cbfd` | 1 | 2 | `keep` | dirty worktree |
| `cce2` | 6 | 0 | `keep` | dirty worktree |
| `cd4a` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `cdd5` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `ce37` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `ce86` | 45 | 0 | `keep` | dirty worktree |
| `d0d4` | 45 | 0 | `keep` | dirty worktree |
| `d1be` | 45 | 0 | `keep` | dirty worktree |
| `d266` | 1 | 2 | `keep` | dirty worktree |
| `d442` | 4 | 2 | `keep` | dirty worktree |
| `d4af` | 47 | 0 | `keep` | dirty worktree |
| `d5c1` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `d771` | 66 | 0 | `keep` | dirty worktree |
| `d77b` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `da6c` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `dbf3` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `dcb5` | 45 | 0 | `keep` | dirty worktree |
| `dd1c` | 8 | 2 | `keep` | dirty worktree |
| `de23` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `de58` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `de7c` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `df29` | 45 | 0 | `keep` | dirty worktree |
| `dfa0` | 45 | 0 | `keep` | dirty worktree |
| `e01e` | 66 | 0 | `keep` | dirty worktree |
| `e4f3` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `e5c3` | 66 | 0 | `keep` | dirty worktree |
| `e61e` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `e728` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `e7ba` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `e8d8` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `e91d` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `eb8c` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `ebc7` | 2 | 0 | `keep` | dirty worktree |
| `ebc8` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `ee14` | 45 | 0 | `keep` | dirty worktree |
| `ee7a` | 0 | 2 | `keep` | unique commits |
| `eef1` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `ef5c` | 66 | 0 | `keep` | dirty worktree |
| `f023` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `f032` | 45 | 0 | `keep` | dirty worktree |
| `f399` | 66 | 0 | `keep` | dirty worktree |
| `fa48` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `fd74` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `fd75` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `fe31` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `feb9` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `ff43` | 30 | 0 | `keep` | dirty worktree |

## Manual Command (Plan Mode)

```bash
rm -rf "/Users/aaronmontgomery/.codex/worktrees/0120"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/054c"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/070f"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/0753"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/09f3"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/0c72"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/0db0"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/0dcf"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/0f9b"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/10c5"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/18d3"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/1ca3"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/2934"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/2983"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/2b26"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/2f83"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/3117"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/3196"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/323a"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/32cd"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/33fc"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/34cb"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/40d9"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/4111"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/4601"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/4933"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/4a03"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/5208"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/53de"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/5492"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/5536"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/55dd"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/5612"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/5636"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/5995"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/5afe"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/5e1a"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/6063"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/61e2"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/632e"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/63d4"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/64e8"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/6a5e"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/6e42"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/70ea"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/7148"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/7361"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/73dc"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/7446"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/7aca"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/7e7d"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/7ef7"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/7f10"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/8743"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/8750"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/879a"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/8a3f"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/8adc"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/8e59"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/913d"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/9204"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/9554"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/98ab"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/9ee8"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/a864"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/a930"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/a9fb"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/acd8"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/ace3"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/b8ad"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/ba3f"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/bc9b"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/bec3"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/c377"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/c40e"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/c684"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/c885"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/cae7"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/cd4a"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/cdd5"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/ce37"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/d5c1"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/d77b"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/da6c"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/dbf3"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/de23"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/de58"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/de7c"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/e4f3"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/e61e"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/e728"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/e7ba"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/e8d8"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/e91d"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/eb8c"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/ebc8"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/eef1"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/f023"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/fa48"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/fd74"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/fd75"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/fe31"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/feb9"
```

## Notes

- This plan intentionally excludes `bad1` unless you remove it from `--exclude-ids`.
- Re-run this script before any destructive cleanup to account for new commits.
