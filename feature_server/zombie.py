
from pyspades.constants import *
    from commands import add, admin, alias
    from twisted.internet.task import LoopingCall
    from twisted.internet import reactor
    import random

    #CONSTANTS - DON'T TOUCH THESE
    HUMAN = 0
    ZOMBIE = 1
    HIDE_COORD = (0,0,63)

    #CONFIGURABLES
    LOBBY_TIME = 60 #The amount of time the lobby lasts in seconds
    ROUND_TIME = 180 #The amount of time a round lasts in seconds
    ZOMBIE_RIFLE_RESIST = 2 #Divisor for how much damage a zombie takes against rifle
    ZOMBIE_SMG_RESIST = 5 #Divisor for how much damage a zombie takes against smg
    ZOMBIE_SHOTGUN_RESIST = 2 #Divisor for how much damage a zombie takes against shotgun
    ZOMBIE_SHOVEL_RESIST = 10 #Divisor for how much damage a zombie takes against shovel
    ZOMBIE_HIT_PENALTY = 3 #Divisor for how much damage a zombie does with shovel
    Z_FALL_IMMUNE = True #Are zombies immune to fall damage


    ## FUNCTIONS
    def startMatch(protocol):

        protocol.MATCH_RUNNING = True

    def stopMatch(protocol):

        protocol.MATCH_RUNNING = False


    def randomSpawn(spawns):

        i = random.randint(0,(len(spawns)-1))
       return spawns[i].getSpawnPosition()

   def getTeamDead(team):
       for player in team.get_players():
           if player.state == HUMAN:
               return False
       return True

   def roundWin(killer):

       if killer != None:

           killer.take_flag()
          killer.capture_flag()

    def chooseZombie(protocol):

        for player in protocol.blue_team.get_players():
            protocol.PLAYER_LIST.append(player)
       for player in protocol.green_team.get_players():
           protocol.PLAYER_LIST.append(player)

       i = random.randint(0,len(protocol.PLAYER_LIST)-1)

       protocol.PLAYER_LIST[i].state = ZOMBIE
       protocol.send_chat(protocol.PLAYER_LIST[i].name + " is the starting zombie")

    def setAllHuman(protocol):

        for player in protocol.blue_team.get_players():
            protocol.PLAYER_LIST.append(player)
       for player in protocol.green_team.get_players():
           protocol.PLAYER_LIST.append(player)

       for i in xrange(0, len(protocol.PLAYER_LIST)-1):
           protocol.PLAYER_LIST[i].state = HUMAN

    ## FUNCTIONS

    ## CLASSES
    class ZombieSpawn:

        def __init__(self,x,y,z):
            self.spawn = (x,y,z)

       def getSpawnPosition(self):
           return self.spawn

    class HumanSpawn:

        def __init__(self,x,y,z):
            self.spawn = (x,y,z)

       def getSpawnPosition(self):
           return self.spawn
    ## CLASSES


    ## COMMANDS   

    #Get if MATCH_RUNNING is true or false
    @alias("gs")
    @admin
    def getstatus(connection):

        if connection.protocol.MATCH_RUNNING:
            connection.send_chat("Match Running")
       elif not connection.protocol.MATCH_RUNNING:
           connection.send_chat("Match Not Running")
    add(getstatus)

    #Get you current infection status
    @alias("state")
    @admin
    def getstate(connection):

        if connection.state == HUMAN:
            connection.send_chat("You are a human")
       elif connection.state == ZOMBIE:
           connection.send_chat("You are a zombie")
    add(getstate)

    #Set your state to zombie
    @alias("zom")
    @admin
    def becomezombie(connection):

        connection.state = ZOMBIE
       connection.send_chat("You have become a zombie")
    add(becomezombie)

    #Set your state to human
    @alias("hum")
    @admin
    def becomehuman(connection):

        connection.state = HUMAN
       connection.send_chat("You have become a human")
    add(becomehuman)

    #Set MATCH_RUNNING true
    @alias("sr")
    @admin
    def startround(connection):
        startMatch(connection.protocol)
       connection.send_chat("Setting MATCH_RUNNING to true")
    add(startround)

    #Set MATCH_RUNNING false
    @alias("er")
    @admin
    def endround(connection):
        stopMatch(connection.protocol)
       connection.send_chat("Setting MATCH_RUNNING to false")
    add(endround)

    #Pick zombies
    @alias("pz")
    @admin
    def pickzombies(connection):
        chooseZombie(connection.protocol)
    add(pickzombies)
    ## COMMANDS

    def apply_script(protocol, connection, config):

        class InfConnection(connection):

            def on_join(self):

                #If a match is running, people who join become zombies
             if self.protocol.MATCH_RUNNING:
                 self.state = ZOMBIE
             else:
                 self.state = HUMAN

             return connection.on_join(self)


         def on_spawn_location(self, pos):

             if not self.protocol.MATCH_RUNNING:
                 setAllHuman(self.protocol)

             ext = self.protocol.map_info.extensions

             #Humans on humans team, Zombies on zombie team
             if self.protocol.MATCH_RUNNING:
                 if self.state == HUMAN:
                     self.team = self.protocol.blue_team
                elif self.state == ZOMBIE:
                    self.team = self.protocol.green_team

             #While match is running place people in appropriate spawn locations
             if self.protocol.MATCH_RUNNING:

                 if self.state == ZOMBIE:
                     return randomSpawn(self.protocol.zombieSpawns)

                elif self.state == HUMAN:
                    return self.protocol.humanSpawn


          def on_hit(self, hit_amount, hit_player, type, grenade):

              #Stop damage if match is not running
             if not self.protocol.MATCH_RUNNING:
                 return False
             else:

                 #ZOMBIE DAMAGE MODIFIERS
                if self.state == HUMAN and hit_player.state == ZOMBIE:

                    if self.tool == WEAPON_TOOL:

                        if self.weapon == RIFLE_WEAPON:
                            return hit_amount/ZOMBIE_RIFLE_RESIST
                      elif self.weapon == SMG_WEAPON:
                          return hit_amount/ZOMBIE_SMG_RESIST
                      elif self.weapon == SHOTGUN_WEAPON:
                          return hit_amount/ZOMBIE_SHOTGUN_RESIST


                   elif self.tool == SPADE_TOOL:
                       return hit_amount/ZOMBIE_SHOVEL_RESIST

                #HUMAN DAMAGE MODIFIERS
            elif self.state == ZOMBIE and hit_player.state == HUMAN:

                if self.tool == SPADE_TOOL:
                    return hit_amount/ZOMBIE_HIT_PENALTY
                else:
                    return False

                else:

                    return connection.on_hit(self, hit_amount, hit_player, type, grenade)


          def on_kill(self, killer, type, grenade):

              #If a match is running, handle player infections
             if self.protocol.MATCH_RUNNING:

                 if self.state == HUMAN:

                     if killer != None:

                         if killer.state == ZOMBIE:

                             self.state = ZOMBIE
                         self.send_chat("You have been infected")
                         killer.send_chat("You infected " + self.name)

             self.protocol.check_round_end(killer)
             print("CHECKING ROUND END")

             return connection.on_kill(self, killer, type, grenade)

         def on_fall(self, damage):

             if not self.protocol.MATCH_RUNNING:
                 return False

             if self.protocol.MATCH_RUNNING:
                 if self.state == ZOMBIE:
                     return False
                else:
                    return connection.on_fall(self, damage)


          def on_block_build_attempt(self, x, y, z):

              #Stop building
             return False


         def on_block_destroy(self, x, y, z, mode):

             #Stop block destruction
             return False


         def on_grenade(self, time_left):

             #Stop zombies using grenade
             if self.state == ZOMBIE:
                 return False
             else:
                 return connection.on_grenade(self, time_left)


       class InfProtocol(protocol):

           game_mode = CTF_MODE

          def on_advance(self, map):

              self.PLAYER_LIST = []

             setAllHuman(self)

             self.countdown = reactor.callLater(LOBBY_TIME, self.lobbyTimer)


          def lobbyTimer(self):

              count = 0

             for team in (self.green_team, self.blue_team):
                 count += team.count()

             if count >= 2:
                 self.beginRound()
             else:
                 self.send_chat("A GAME REQUIRES ATLEAST 2 PEOPLE")
                print("NOT ENOUGH PLAYERS")
                self.countdown = reactor.callLater(LOBBY_TIME, self.lobbyTimer)


          def on_map_change(self, map):

              self.PLAYER_LIST = []

             self.MATCH_RUNNING = False

             if self.map_info.extensions['infection']:

                 ext = self.map_info.extensions
                self.zombieSpawns = []
                self.humanSpawn = ext['human_spawn']

                for spawns in ext['zombie_spawns']:
                    self.zombieSpawns.append(ZombieSpawn(*spawns))

          def check_round_end(self, killer = None, message = True):

              if self.MATCH_RUNNING:

                  if getTeamDead(self.blue_team):
                      self.winRound(killer)
                   return


          def winRound(self, killer):

              if killer.state == ZOMBIE:
                  self.roundTimer.cancel()

             print("ROUND WON")
             self.MATCH_RUNNING = False
             roundWin(killer)
             setAllHuman(self)
             self.MATCH_RUNNING = False
             return

         def beginRound(self):

             chooseZombie(self)
             self.roundTimer = reactor.callLater(ROUND_TIME, self.humanWin)

             for player in self.PLAYER_LIST:
                 player.kill()

             self.MATCH_RUNNING = True

          def humanWin(self):

              for player in self.blue_team.get_players():
                  if player.state == HUMAN:
                      self.winRound(player)
                   return

          def on_base_spawn(self, x, y, z, base, entity_id):
              return HIDE_COORD

          def on_flag_spawn(self, x, y, z, flag, entity_id):
              return HIDE_COORD

       return InfProtocol, InfConnection or None
