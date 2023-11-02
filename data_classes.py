class Player:
    def __init__(self, name, position, id, team, projections=None, owner_name=None, score_settings=None):
        self.name = name
        self.position = position
        self.id = id
        self.team = team
        self.owner_name = owner_name
        
        # A list of dictionaries, each dictionary representing a week's projections
        self.projections = projections if projections else []
        
        # Assuming you want to include scoring_settings as an instance variable
        self.scoring_settings = score_settings if score_settings else {}
        
        # Ensuring that the list of projections has entries for all weeks
        for i in range(18):  
            if len(self.projections) <= i or self.projections[i] is None:
                self.projections.append({key: 0 for key in self.scoring_settings.keys()})

    def update_projections(self, week, new_projections):
        """
        Updates the player's projections for the specified week.
        If new_projections is None, it will default the week's projection to all zeros.
        """
        week_index = int(week) - 1  # Convert week to integer
        if week_index < 0 or week_index > len(self.projections) - 1:
            raise ValueError(f"Invalid week index: {week_index + 1}. Expected 1-18.")


        if new_projections:
            self.projections[week_index] = new_projections
        else:
            self.projections[week_index] = {key: 0 for key in self.scoring_settings.keys()}

    

        
class Team:

    def __init__(self):
        self.name = None
        self.players = []
        self.current_max_pf = 0
        self.current_max_pf_players = []
        self.wins = 0
        self.losses = 0
        self.ties = 0
        self.points_for = 0
        self.points_against = 0
        
        
class FinalOutput:

    def __init__(self):
        self.current_max_pf = {}
        self.remaining_max_pf = {}
        self.total_max_pf = {}
        
        self.predicted_draft_order = []
        self.predicted_playoff_teams = []
        self.predicted_champion = []
    
