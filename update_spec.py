with open("SPEC.md", "r") as f:
    content = f.read()

content = content.replace("Version: 0.1.3", "Version: 0.1.4")

with open("SPEC.md", "w") as f:
    f.write(content)
