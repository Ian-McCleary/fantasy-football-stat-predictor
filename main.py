import urllib.request as urllib2

from bs4 import BeautifulSoup
from kivy.app import App
from kivy.garden.graph import Graph, MeshLinePlot
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.listview import ListItemButton
from math import sin
from sklearn import linear_model
import numpy as np
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.factory import Factory
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock

#Global lists
position_list = []
player_list = []
plot_list = []





class PlayerSelected(ListItemButton):
    pass  


class mainScreenLayout(GridLayout):
    #Kivy objects that update UI when changed in python automatically
    ready_player_list = ObjectProperty()
    pyGraph = ObjectProperty()
    search_bar_input = ObjectProperty()
    position_dropdown = Spinner()
    g_weeks_retrieved = 0
    

    def search_button(self):

        self.ready_player_list.adapter.data = []

        #Check to see which positions are selected in dropdown then repopulates listview
        if (self.position_dropdown.text == 'All Positions'):
            for i in range(len(position_list)):
                for j in range(len(position_list[i])):
                    self.ready_player_list.adapter.data.extend([position_list[i][j][0]])

        if (self.position_dropdown.text == 'Quarter Backs'):
            for j in range(len(position_list[0])):
                self.ready_player_list.adapter.data.extend([position_list[0][j][0]])
            
        if (self.position_dropdown.text == 'Running Backs'):
            for j in range(len(position_list[1])):
                self.ready_player_list.adapter.data.extend([position_list[1][j][0]])
            
        if (self.position_dropdown.text == 'Wide Recievers'):
            for j in range(len(position_list[2])):
                self.ready_player_list.adapter.data.extend([position_list[2][j][0]])
            
        if (self.position_dropdown.text == 'Tight Ends'):
            for j in range(len(position_list[3])):
                self.ready_player_list.adapter.data.extend([position_list[3][j][0]])
            
        if (self.position_dropdown.text == 'Kickers'):
            for j in range(len(position_list[4])):
                self.ready_player_list.adapter.data.extend([position_list[4][j][0]])

        #Check to see if search bar is empty, if not show players with substring in name
        if self.search_bar_input != "":
            temp_search_list = []
            for i in range(len(self.ready_player_list.adapter.data)):
                if (self.search_bar_input.text in self.ready_player_list.adapter.get_data_item(i).lower()):
                    temp_search_list.append(self.ready_player_list.adapter.get_data_item(i))
                    print("found player" + self.search_bar_input.text)
            self.ready_player_list.adapter.data = temp_search_list

        



    def position_selected_dropdown(self):
        pass

    #Reorganize player data then make linear regression calculations.
    #Returns slope and y intercept. Used to graph y=mx+b
    def lin_reg_list(self, player_stats):
        weeks_list = []
        score_list = []
        reg_obj = linear_model.LinearRegression()
        for i in range(1, len(player_stats)):
            weeks_list.append([player_stats[i][0]])
            score_list.append(player_stats[i][1])
        pred = np.array([11,0])
        pred.reshape(1,-1)
        #Linear Regression prediction using player stats
        reg_obj.fit(weeks_list, score_list)
        reg_obj.predict(weeks_list)
        print(reg_obj.coef_)
        print(reg_obj.intercept_)

        return [float(reg_obj.coef_), reg_obj.intercept_]

        
    
    #Plots player stats and lin reg lines. Called by selectedFromList when graph button clicked
    def update_graph(self, player_name):
        #Clear all previous lines on graph
        if len(plot_list) > 0:
            for i in range(len(plot_list)):
                self.pyGraph.remove_plot(plot_list[i]) 
            plot_list.clear()

        plot = MeshLinePlot(color=[1, 0, 0, 1])
        reg_plot = MeshLinePlot(color=[0, 1, 0, 1])

        for i in range(len(position_list)):
            for j in range(len(position_list[i])):
                if position_list[i][j][0] == player_name:
                    print("found " + player_name)
                    #plot for player stats
                    plot.points = [(position_list[i][j][h][0], position_list[i][j][h][1]) for h in range(1,len(position_list[i][j]))]
                    self.pyGraph.add_plot(plot)
                    plot_list.append(plot)

                    #Plot for lin reg line. y=mx+b
                    reg_slope = self.lin_reg_list(position_list[i][j])[0]
                    reg_y_intercept = self.lin_reg_list(position_list[i][j])[1]

                    reg_plot.points = [(1, reg_y_intercept), (self.g_weeks_retrieved, reg_slope * self.g_weeks_retrieved + reg_y_intercept)]
                    self.pyGraph.add_plot(reg_plot)
                    plot_list.append(reg_plot)
                    break
        return str(player_name) + ' not found'



    #initialize program and inflate mainScreenLayout 
    def __init__(self, **kwargs):
        super(mainScreenLayout, self).__init__(**kwargs)
        self.position_dropdown.values = ["All Positions", "Quarter Backs", "Running Backs", "Wide Recievers", "Tight Ends", "Kickers"]

    #When graph button clicked, get the players name from the listview
    def selectedFromList (self, *args):
        if self.ready_player_list.adapter.selection:
            selection = self.ready_player_list.adapter.selection[0].text
            print(selection)
            self.update_graph(selection)

    #Adds player stats from web scrap into multiple nested lists
    def addPlayerData(self,name, points, week_cycle):
        week_stat = [week_cycle, float(points)]
        stat_list = [name, week_stat]

        #Search for already exsisting players in list. If none, add name and pts. If found, just add pts to their list
        for sub_list in player_list:
            if name in sub_list:
                sub_list.append(week_stat)
                break
        else:
            player_list.append(stat_list)
            self.ready_player_list.adapter.data.extend([name])
        

    #After 1 positions has data for all weeks, add all stats to another list.
    #position lists order = QB,RB,WR,TE,Kicker
    def addPlayerListForAllWeeks(self):
        #Clones and then adds player_list to position_list. Each element in  pos list is a different position
        position_list.append(player_list[:])
        player_list.clear()

    #Web scraping function. Cycles through 5 positions and x weeks of data.
    #Called by Refresh stats button  
    def getPlayerStats(self, positions_int, weeks_int):

        url_cycle = 0
        self.g_weeks_retrieved = weeks_int
        self.ready_player_list.adapter.data = []
        
        while (url_cycle < positions_int):
            print("URL CYCLE", url_cycle)
            week_cycle = 1
            
            while week_cycle < weeks_int:
                print("WEEK CYCLE", week_cycle)
                position_urls = ["https://www.footballdb.com/fantasy-football/index.html?pos=QB&yr=2018&wk="+ str(week_cycle) + "&rules=1","https://www.footballdb.com/fantasy-football/index.html?pos=RB&yr=2018&wk="+ str(week_cycle) + "&rules=1", 
                                "https://www.footballdb.com/fantasy-football/index.html?pos=WR&yr=2018&wk="+ str(week_cycle) + "&rules=1","https://www.footballdb.com/fantasy-football/index.html?pos=TE&yr=2018&wk="+ str(week_cycle) + "&rules=1",
                                "https://www.footballdb.com/fantasy-football/index.html?pos=K&yr=2018&wk="+ str(week_cycle) + "&rules=1"]
                
                # query the website and return the html to the variable current_page
                current_page = urllib2.urlopen(position_urls[url_cycle]) #position_urls[url_cycle]
                
                # parse the html using beautiful soup and store in variable soup
                #searches for first table row with class row0 right, then procedes to next table 
                soup = BeautifulSoup(current_page, "html.parser")
                table_row_init = soup.find("tr", attrs={"class": "row0 right"})
                next_table_row = table_row_init
                number_of_players = 0
                i=0
                while ( i < 120):
                    name_ahref2 = next_table_row.find("a")
                    if name_ahref2 == None:
                        break
                    name2 = name_ahref2.text.strip() # strip() is used to remove starting and trailing
                    number_of_players += 1
                    week_points2 = next_table_row.find("td", attrs={"class": "hilite"}).text.strip()
                    next_table_row = next_table_row.find_next("tr")
                    self.addPlayerData(name2, week_points2, week_cycle)
                    i+=1
                
                print("Number of players for week ", week_cycle, ": ", number_of_players)
                week_cycle += 1
                
            
            url_cycle += 1
            self.addPlayerListForAllWeeks()
            #self.updateProgressBar()
            #self.update_bar_trigger()


#app class used by kivy to create app build
class fantasyApp(App):
    def build(self):
        return mainScreenLayout()
    
    
if __name__ == "__main__":
    fantasyApp().run()


    
