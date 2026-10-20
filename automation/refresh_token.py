# -*- coding: utf-8 -*-
"""長期トークン（60日）を延長し、新しいトークンを GitHub Secret に書き戻す。
   graph.instagram.com/refresh_access_token（ig_refresh_token）。24時間以上経過・未失効のトークンのみ延長可。
   Secret の更新には GH_PAT（repo 権限の Personal Access Token）が必要。"""
import json, os, sys, urllib.request, subprocess
tok=os.environ["IG_ACCESS_TOKEN"]
with urllib.request.urlopen(f"https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token={tok}", timeout=30) as r:
    d=json.loads(r.read())
new=d.get("access_token"); days=int(d.get("expires_in",0))//86400
if not new: sys.exit(f"refresh failed: {d}")
print(f"refreshed; valid for {days} days")
if new!=tok:
    r=subprocess.run(["gh","secret","set","IG_ACCESS_TOKEN","--body",new,"-R",os.environ["GITHUB_REPOSITORY"]],
                     env={**os.environ,"GH_TOKEN":os.environ["GH_PAT"]},capture_output=True,text=True)
    print("secret updated" if r.returncode==0 else f"secret update failed: {r.stderr}")
    if r.returncode: sys.exit(1)
