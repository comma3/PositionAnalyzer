using System;
using System.Reflection;
using System.IO;
using DemoInfo;
using System.Collections.Generic;
using System.Linq;

namespace CSPositionAnalyzer
{
    class MainClass
    {
        public static void Main()
        {          
            List<string> argslist = new List<string>();
            string line;
            int filecount = 0;
            while ((line = Console.ReadLine()) != null && line != "")
            {
                int filelength = line.Split('.').Length;
                if (filelength < 2)
                {
                    continue; //skip folders
                } else if (line.Split('.')[filelength-1] == "dem")
                {
                    filecount += 1;
                    argslist.Add(line);
                }
            }

            

            //leaving this for now to see if anything else sneaks by
            argslist.ForEach(Print);

            // First, check wether the user needs assistance:
            if (argslist.Count == 0 || argslist[0] == "--help")
            {
                PrintHelp();
                return;
            }

            Console.WriteLine("Processing " + filecount + " demo files");

            // Every argument is a file, so let's iterate over all the arguments
            // So you can call this program like
            // > StatisticsGenerator.exe hello.dem bye.dem
            // It'll generate the statistics.
            foreach (var fileName in argslist)
            {
                // Okay, first we need to initalize a demo-parser
                // It takes a stream, so we simply open with a filestream
                using (var fileStream = File.OpenRead(fileName))
                {
                    // By using "using" we make sure that the fileStream is properly disposed
                    // the same goes for the DemoParser which NEEDS to be disposed (else it'll
                    // leak memory and kittens will die). 


                    Console.WriteLine("Parsing demo " + fileName);

                    using (var parser = new DemoParser(fileStream))
                    {
                        // So now we've initialized a demo-parser. 
                        // let's parse the head of the demo-file to get which map the match is on!
                        // this is always the first step you need to do.
                        parser.ParseHeader();

                        //might want to know cs vs de later but just using short names for now
                        string fullmap = parser.Map;
                        string map = fullmap.Split('_')[1];
        
                        //Generate high entropy name for unique identification
                        //This shortens filenames and ensures that files will occur alphabetically
                        string matchcode = GenerateString(6);

                        // And now, generate the filename of the resulting files
                        string outputFileNamePlayerData =  matchcode + "_" + map + "_playerdata.csv";
                        string outputFileNameNades =  matchcode + "_" + map + "_nadedata.csv";
                        string outputFileNameGameData =  matchcode + "_" + map + "_gamedata.csv";
                        string outputFileNameMatchInfo = matchcode + "_" + map + "_matchinfo.csv"; //maybe put steamids/playernames in here

                        // and open it. 
                        var outputStreamPlayerData = new StreamWriter(outputFileNamePlayerData);
                        var outputStreamNades = new StreamWriter(outputFileNameNades);
                        var outputStreamGameData = new StreamWriter(outputFileNameGameData);
                        var outputStreamMatchInfo = new StreamWriter(outputFileNameMatchInfo);

                        //And write a header so you know what is what in the resulting file
                        outputStreamPlayerData.WriteLine(GenerateCSVHeader());
                        outputStreamNades.WriteLine(string.Format("Tick,Time,Round,CTScore,TScore,Thrower,Type,XPos,YPos,ZPos"));
                        outputStreamGameData.WriteLine(string.Format("Tick,Time,Round,CTScore,TScore,Reason"));
                        outputStreamMatchInfo.WriteLine(string.Format("Match Code,Map,Avg Rank,Team 1,Team 2, File Name"));

                        // Cool! Now let's get started generating the analysis-data. 
                        //Let's just declare some stuff we need to remember
                        // Here we remember whether the match has started yet. 
                        bool hasMatchStarted = false;
                        bool hasRoundStarted = false;

                        List<Player> ingame = new List<Player>();

                        string CTTeamName = "Error";
                        string TTeamName = "Error";

                        //getting some tickrate information to limit the amount of data to roughly half-second intervals
                        //this value isn't exact so we are going to manually set it for 32 and 64 tick demos by splitting somewhere in the middle
                        float tickrate = parser.TickRate;
                        

                        //setting 16 as the default condition
                        double halfsecond = Math.Round(0.5 * tickrate);
                        Console.WriteLine("Interval : " + halfsecond);
                        //putting split values at 55 and 110
                        //So far most demos are 32 or 64 but I've also seen 25 and 128
                        //ultimately we'll get the timestamp at the end so this isn't terribly important - just trying to limit the size of the database to roughly half seconds

                        //if (tickrate > 55 && tickrate < 110) 
                        //{
                        //    halfsecond = 32;
                        //} 
                        //else if (tickrate > 110)
                        //{
                        //    halfsecond = 64;
                        //}

                        //  
                        // Since most of the parsing is done via "Events" in CS:GO, we need to use them. 
                        // So you bind to events in C# as well. 
                        // AFTER we have bound the events, we start the parser!

                        //might be worthwhile trying to prevent multiple starts. I think this causes some issues in pistol round data (i.e., end of warmup is sometimes lumped into knife/pistol rounds)
                        parser.MatchStarted += (sender, e) =>
                        {
                            hasMatchStarted = true;
                            //Okay let's output who's really in this game!

                            Console.WriteLine("{0}   Participants: {1}  vs  {2} ", matchcode, parser.CTClanName, parser.TClanName);

                            //Write Player Names and SteamIDs to a file - Only want this once
                            //foreach (var player in parser.PlayingParticipants)
                            //{
                            //outputStreamPlayerInfo.WriteLine(string.Format("{0}, {1}, {2}", player.Name, player.SteamID, player.EntityID)); 
                            //might be able to get ranks from csgosquad.com
                            //Use entityID to tie players in GameData database to moveset database
                            //}

                            CTTeamName = parser.CTClanName;
                            TTeamName = parser.TClanName;

                            // Okay, problem: At the end of the demo
                            // a player might have already left the game,
                            // so we need to store some information
                            // about the players before they left :)
                            ingame.AddRange(parser.PlayingParticipants);
                        };

                        parser.FreezetimeEnded += (sender, e) => //cut out buy time and timeouts
                        {
                            hasRoundStarted = true;
                        };

                        parser.TickDone += (sender, e) =>
                        {
                            if (!hasMatchStarted)
                                return;

                            int tick = parser.CurrentTick;

                            if (tick % halfsecond == 0 && hasRoundStarted)
                            {
                                float time = tick * parser.TickTime;
                                foreach (var player in parser.PlayingParticipants) //this is supposed to print this information every 16 ticks (~0.5 s or 0.25 s for 64 tick) for each player
                                {
                                    Team playerteam = player.Team;
                                    if (player.IsAlive && !player.Disconnected && (int)playerteam != 1)
                                    {
                                        int playerID = player.EntityID;
                   
                                        string StrTick = tick.ToString();

                                        Vector playerpos = player.Position;
                                        bool playerducking = player.IsDucking;

                                        int playerhp = player.HP;
                                        int playerarmor = player.Armor;
                                        bool playerhelmet = player.HasHelmet;
                                        bool playerdefuse = player.HasDefuseKit;

                                        //extra equipment is stored in one cell so that csv rows have the same length
                                        string allweapons = "";
                                        foreach (Equipment w in player.Weapons)
                                            {
                                            if (w.Weapon.ToString() == "Smoke" || w.Weapon.ToString() == "Flash" || w.Weapon.ToString() == "Molotov" || w.Weapon.ToString() == "Incendiary" || w.Weapon.ToString() == "HE" || w.Weapon.ToString() == "Decoy" || w.Weapon.ToString() == "Bomb")
                                                allweapons = allweapons + " " + w.Weapon;
                                            }

                                        EquipmentElement playeractiveweapon = player.ActiveWeapon.Weapon;

                                        PrintTickInfo(parser, outputStreamPlayerData, StrTick, time, playerteam, playerID, playerpos, playerducking, playerhp, playerarmor, playerhelmet, playerdefuse, playeractiveweapon, allweapons);
                                    }
                                }
                            }
                        };

                        //nades are recorded as events
                        parser.SmokeNadeStarted += (sender, e) =>
                        {
                            if (!hasMatchStarted)
                                return;

                            int tick = parser.CurrentTick;
                            float time = tick * parser.TickTime;

                            int CTScore = parser.CTScore;
                            int TScore = parser.TScore;
                            int Round = CTScore + TScore + 1;

                            int thrower = e.ThrownBy.EntityID;

                            string StrTick = tick.ToString();

                            Vector smokeposition = e.Position;

                            outputStreamNades.WriteLine(string.Format("{0}, {1}, {2}, {3}, {4}, {5},Smoke Nade, {6}", StrTick, time, Round, CTScore, TScore, thrower, smokeposition)); //Nades are placed in PlayerID column so that iterating over that column will correctly differentiate nades from players. Thrown player is placed in team column. Will probably be ignored, but this information is retained.
                        };

                        parser.FireNadeStarted += (sender, e) =>
                            {
                                if (!hasMatchStarted)
                                    return;

                                int tick = parser.CurrentTick;
                                float time = tick * parser.TickTime;

                                int CTScore = parser.CTScore;
                                int TScore = parser.TScore;

                                int Round1 = CTScore + TScore + 1;

                                //int thrower = e.ThrownBy.EntityID; //from the class /// This currently *doesn't* contain who it threw since this is for some weird reason not networked

                                string StrTick = tick.ToString();

                                Vector fireposition = e.Position;
                                //Changed thrownby to 98 - python will want an INT in that column.
                                //99 in bomb planted
                                outputStreamNades.WriteLine(string.Format("{0}, {1}, {2}, {3}, {4},98,Fire Nade, {5}", StrTick, time, Round1, CTScore, TScore, fireposition)); //Nades are placed in PlayerID column so that iterating over that column will correctly differentiate nades from players. Thrown player is placed in team column. Will probably be ignored, but this information is retained.
                            };

                        parser.DecoyNadeStarted += (sender, e) =>
                        {
                            if (!hasMatchStarted)
                                return;

                            int tick = parser.CurrentTick;
                            float time = tick * parser.TickTime;

                            int CTScore = parser.CTScore;
                            int TScore = parser.TScore;
                            int Round = CTScore + TScore + 1;

                            int thrower = e.ThrownBy.EntityID;

                            string StrTick = tick.ToString();

                            Vector decoyposition = e.Position;

                            outputStreamNades.WriteLine(string.Format("{0}, {1}, {2}, {3}, {4}, {5},Decoy Nade, {6}", StrTick, time, Round, CTScore, TScore, thrower, decoyposition)); //Nades are placed in PlayerID column so that iterating over that column will correctly differentiate nades from players. Thrown player is placed in team column. Will probably be ignored, but this information is retained.
                        };

                        parser.FlashNadeExploded += (sender, e) =>
                        {
                            if (!hasMatchStarted)
                                return;

                            int tick = parser.CurrentTick;
                            float time = tick * parser.TickTime;

                            int CTScore = parser.CTScore;
                            int TScore = parser.TScore;
                            int Round = CTScore + TScore + 1;

                            int thrower = e.ThrownBy.EntityID;

                            string StrTick = tick.ToString();

                            Vector flashposition = e.Position;

                            outputStreamNades.WriteLine(string.Format("{0}, {1}, {2}, {3}, {4}, {5},Flash Nade, {6}", StrTick, time, Round, CTScore, TScore, thrower, flashposition)); //Nades are placed in PlayerID column so that iterating over that column will correctly differentiate nades from players. Thrown player is placed in team column. Will probably be ignored, but this information is retained.
                        };

                        parser.ExplosiveNadeExploded += (sender, e) =>
                        {
                            if (!hasMatchStarted)
                                return;

                            int tick = parser.CurrentTick;
                            float time = tick * parser.TickTime;

                            int CTScore = parser.CTScore;
                            int TScore = parser.TScore;
                            int Round = CTScore + TScore + 1;

                            int thrower = e.ThrownBy.EntityID;

                            string StrTick = tick.ToString();

                            Vector HEposition = e.Position;

                            outputStreamNades.WriteLine(string.Format("{0}, {1}, {2}, {3}, {4}, {5},HE Nade, {6}", StrTick, time, Round, CTScore, TScore, thrower, HEposition)); //Nades are placed in PlayerID column so that iterating over that column will correctly differentiate nades from players. Thrown player is placed in team column. Will probably be ignored, but this information is retained.
                        };

                        parser.BombPlanted += (sender, e) => //Will have to get position from previous tick - just use posiiton have player with C4 as active weapon
                        {
                            if (!hasMatchStarted)
                                return;

                            int tick = parser.CurrentTick;
                            float time = tick * parser.TickTime;

                            int CTScore = parser.CTScore;
                            int TScore = parser.TScore;
                            int Round = CTScore + TScore + 1;

                            string StrTick = tick.ToString();

                            //zeros are for position so these rows are the same length as other nades
                            //Changed thrownby to 99 - python will want an INT in that column.
                            outputStreamNades.WriteLine(string.Format("{0}, {1}, {2}, {3}, {4},99,Bomb Planted,0,0,0", StrTick, time, Round, CTScore, TScore));
                        };

                        parser.RoundEnd += (sender, e) =>
                        {
                            if (!hasMatchStarted)
                                return;

                            RoundEndReason reason = e.Reason;
                            Team winner = e.Winner;

                            int tick = parser.CurrentTick;
                            float time = tick * parser.TickTime;


                            int CTScore = parser.CTScore;
                            int TScore = parser.TScore;
                            int Round = CTScore + TScore + 1;

                            string StrTick = tick.ToString();

                            outputStreamGameData.WriteLine(string.Format("{0},{1},{2},{3},{4},{5}", StrTick, time, Round, CTScore, TScore, reason));
                        };

                        int ranktotal = 0;
                        int reportedranks = 0;

                        parser.RankUpdate += (sender, e) =>
                        {
                            ranktotal += e.RankOld;
                            reportedranks++;
                        };



                        //Now let's parse the demo!
                        parser.ParseToEnd();


                        //We want to sort these games by average rank so that we can differentiate strats at different levels

                        //Pro games do not contain rank information
                        //Setting pros to 100 for now
                        //In the future, I could make a master list of tier 1, tier 2, etc. pro teams and get the ranks from clan names (contained in demo files)
                        //This step could also be done during DB entry via python program (may be better approach so team names are stored.

                        float avgrank = 100;

                        if (reportedranks != 0)
                        {
                            avgrank = ranktotal / reportedranks;
                        }

                        //parser.CTClanName seems to be empty by here
                        //team names are stored above
                        outputStreamMatchInfo.WriteLine(string.Format("{0},{1},{2},{3},{4},{5}", matchcode, map, avgrank, CTTeamName, TTeamName, fileName));

                        outputStreamPlayerData.Close();
                        outputStreamNades.Close();
                        outputStreamGameData.Close();
                        outputStreamMatchInfo.Close();
                        //outputStreamPlayerInfo.Close();

                    }

                }

            }

        }

        private static void Print(string s)
        {
            Console.WriteLine(s);
        }

        
        static string GenerateCSVHeader() //need to modify for appropriate results 
        {
            return string.Format(
                "{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16}",
                "Tick Number (x2 in HLTV DEMOs)",
                "Time (s)",
                "Round",
                "CT-Score", 
                "T-Score",
                "Player Team",
                "PlayerID",
                "XPos",
                "YPos",
                "ZPos",
                "Ducking",
                "HP",
                "Armor",
                "Helmet",
                "Defuse",
                "Active Weapon",
                "Nades/Bomb");
        }

        static void PrintHelp()
        {
            string fileName = Path.GetFileName((Assembly.GetExecutingAssembly().Location));
            Console.WriteLine("Built based off of CS:GO Demo-Statistics-Generator");
            Console.WriteLine("http://github.com/moritzuehling/demostatistics-creator");
            Console.WriteLine("------------------------------------------------------");
            Console.WriteLine("Usage: {0} [--help] [--scoreboard] file1.dem [file2.dem ...]", fileName);
            Console.WriteLine("--help");
            Console.WriteLine("    Displays this help");
            Console.WriteLine("file1.dem");
            Console.WriteLine("    Path to a demo to be parsed. The resulting csv files will have a high-entropy alphanumeric code ");
            Console.WriteLine("    prepended to the map name and ending with the contents of the file (player data, match data, etc.");
            Console.WriteLine("[file2.dem ...]");
            Console.WriteLine("    The program is designed to pipe an entire folder containing many dem files. Using 'dir /b | CSPA.exe.");
        }

        static void PrintTickInfo(DemoParser parser, StreamWriter outputStream, string currentTick, float time, Team playerteam, int playerID, Vector playerpos, bool playerducking, int playerhp, int playerarmor, bool playerhelmet, bool playerdefuse, EquipmentElement playeractiveweapon, string allweapons)
        {
            outputStream.WriteLine(string.Format("{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14}", //Comma is excluded between 13 and 14 beceause "allweapons" adds commas between elements
            currentTick,
            time,
            parser.CTScore + parser.TScore + 1, //Round number
            parser.CTScore, parser.TScore, //Score
            playerteam, //Ct or t
            playerID, //number to keep track of players
            playerpos, playerducking, //Location info
            playerhp, playerarmor, playerhelmet, //Health/armor
            playerdefuse, //Equipment
            playeractiveweapon, //Selected weapon
            allweapons //need to be single entry so array length is constant
            ));
        }     

        public const string Alphabet =
        "abcdefghijklmnopqrstuvwyxzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";

        static string GenerateString(int size)
        {
            Random rand = new Random();
            char[] chars = new char[size];
            for (int i = 0; i < size; i++)
            {
                chars[i] = Alphabet[rand.Next(Alphabet.Length)];
            }
            return new string(chars);
        }

    }

}

