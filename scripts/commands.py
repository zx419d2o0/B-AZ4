#!/usr/bin/python3
# invoke.tasks.py
import subprocess
import argparse
import shutil
import os


def init():
    print('poetry env info --path')
    subprocess.run(['poetry', 'env', 'info', '--path'])


def test():
    subprocess.run(["poetry", "run", "pytest", "tests", "-v", "-s"])


def compile():
    subprocess.run(["poetry", "run", "python", "setup.py", "build_ext", "--inplace"])
    if os.path.exists('dist'):
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        content = content.replace('from app.bot', 'from bot')
        with open(os.path.join('dist', 'main.py'), 'w', encoding='utf-8') as f:
            f.write(content)


def clean():
    dirs = ["__pycache__", ".pytest_cache", "build", "dist"]
    for dir in dirs:
        if os.path.exists(dir):
            shutil.rmtree(dir)


def deploy():
    subprocess.run(["vc", "./app", "--prod"])


def acp():
    parser = argparse.ArgumentParser(description="add commit push")
    parser.add_argument("message", nargs="?", help="commit message")
    args = parser.parse_args()

    subprocess.run(["git", "pull"])
    msg = args.message or input("commit message:")
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", msg])
    subprocess.run(["git", "push", "--force"])