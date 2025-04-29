################################
#CE SCRIPT N'EST PLUS UTILISE !#
################################



from playsound import playsound
damage_to_player = 0

son1 = "Musique menu principal - 1.mp3"
son2 = "Menu - 2.mp3"
son3 = "son de laser"
son4 = "Musique-vague-1.mp3"
son5 = "Musique-vague-2.mp3"
son6 = "Musique-vague-3.mp3"
son7 = "Musique-vague-4.mp3"
son8 = "Musique-vague-5.mp3"
son9 = "Musique-vague-6.mp3"








def jouer_son():
  while current_screen == "menu" :
    playsound(son1)
  while current_screen == "shop" :
    playsound(son2)
  if shoot() == True :
    playsound("son de tir")
  if explode() == True :
    playsound("explosion1.mp3")
  if check_collision() == True :
    playsound("explosion1.mp3")
  def check_damage_increase():
    if damage_to_player < global damage_to_player :
      playsound("lifelose.mp3")
      damage_to_player = global damage_to_player
  for wave_number in range 1000:
  if wave_number == 0:
    playsound(son4)
  if wave_number == 1:
    playsound(son5)
  if wave_number == 2 :
    playsound(son6)
  if wave_number == 3:
    playsound(son7)
  if wave_number > 3 and wave_number%2 == 0 :
    playsound(son8)
  if wave_number > 3 and wave_number%2 != 0:
    playsound(son9)
  if MOUSEBOUTTONDOWN == True :
    playsound("Son button 1.1.mp3")
    
    
  



    
