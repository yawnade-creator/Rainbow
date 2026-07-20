import random
name = input("给你的海獭起个名字：")
hunger = 50
happiness = 50
backpack = []

print(name + "出现了！")

while True:
    print("---")
    if happiness <= 0:
        print(name + "生气了！咬了你一口然后跑掉了！")
        break
    elif happiness <= 20:
        print("⚠ " + name + "看起来很不开心...")
    print("饥饿值：" + str(hunger) + " 开心值：" + str(happiness))
    action = input("你要做什么？喂食/摸头/给石头/反击/亲亲/捡/捏捏脸/退出：")

    if action == "喂食":
        mood = random.randint(1, 3)
        if mood == 1:
            hunger = hunger - 20
            happiness = happiness + 80
            print(name + "在贝壳里找到珍珠了！")
        elif mood == 2:
            hunger = hunger - 20                             
            happiness = happiness + 20
            print(name + "吃饱了，揉揉脸")
        else:
            hunger = hunger - 20
            happiness = happiness - 10
            print(name + "嫌弃地把食物丢到一边")
    elif action == "摸头":
        mood = random.randint(1, 3)
        if mood == 1:
            happiness = happiness + 30
            print(name + "超级开心地翻肚皮！")
        elif mood == 2:
            happiness = happiness + 10
            print(name + "哼了一声但没躲开")
        else:
            happiness = happiness - 10
            print(name + "心情不好，咬了你一口！")
    elif action == "给石头":
        happiness = happiness + 10
        print(name + "拿石头砸了你一下！")
    elif action == "反击":
        happiness = happiness -20
        print(name + "被打了好痛呜呜呜")
    elif action == "亲亲":
        happiness = happiness +80
        print(name + "被小然亲了嘿嘿")
    elif action == "捡":
        import random
        things = ["石头", "贝壳", "小鱼", "海草"]
        found = random.choice(things)
        backpack.append(found)
        print(name + "捡到了" + found + "！")
    elif action == "捏捏脸":
        if "石头" in backpack:
            backpack.remove("石头")
            happiness = happiness - 10
            print(name + "被捏脸脸！用石头砸你！")
        else:
            print("被捏脸了！想砸你但是没有石头，气鼓鼓的")
    elif action == "退出":
        print(name + "睡着了，拜拜！")
        break
    else:
        print(name + "歪头看着你")
