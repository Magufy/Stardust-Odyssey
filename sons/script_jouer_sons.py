from playsound import playsound
damage_to_player = 0


son1 = "Musique menu principal - 1.mp3"
son2 = "Menu - 2.mp3"
son3 = "son de laser"
son4 = "Musique-vague-1.mp3"
son5 = "Musique-vague-2.mp3"











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
  if wave_number == 1 :
    playsound(son4)
  if wave_number == 2 :
    playsound(son5)
  
    
