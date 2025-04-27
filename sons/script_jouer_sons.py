from playsound import playsound

son1 = "Musique menu principal - 1.mp3"
son2 = "Menu - 2.mp3"












def jouer_son():
  while current_screen == "menu" :
    playsound(son1)
  while current_screen == "shop" :
    playsound(son2)
  if shoot() == True :
    playsound("son de tir")
  if explode() == True :
    playsound(
