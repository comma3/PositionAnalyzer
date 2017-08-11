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
        public static void Main(string[] args)
        {
            // First, check wether the user needs assistance:
            if (args.Length == 0 || args[0] == "--help")
            {
                PrintHelp();
                return;
            }

            // String to store names of bad demos
            string baddemos = "";

            float tickrate;
            double halfsecond;

            // Take a directory as the argumenr and get list of dem files in the directory
            string[] files = Directory.GetFiles(args[0], "*.dem", SearchOption.TopDirectoryOnly);
            Console.WriteLine("=============START=============");
            Console.WriteLine("Processing " + files.Length + " demo files");
            Console.WriteLine("=============START=============");

            // Every argument is a file, so let's iterate over all the arguments
            foreach (var fileName in files)
            {
                // By using "using" we make sure that the fileStream is properly disposed
                // the same goes for the DemoParser which NEEDS to be disposed.

                // First, we need to check for match started event. Some demos trim to after match started event,
                // resulting in data collection never knowing when to start.
                // Unfortunately, have to parse the file first. Fortunately, it's pretty fast.
                // We will also check for bad tickrate data and file length issues here.

                // Assumed to be false until we see one.
                bool hasMatchStartSignal = false;

                // We need to initalize a demo-parser
                // It takes a stream, so we simply open with a filestream
                using (var testfileStream = File.OpenRead(fileName))
                {

                    using (var parser = new DemoParser(testfileStream))
                    {

                        Console.WriteLine("Checking for match start and ticker header   " + fileName);
                        // So now we've initialized a demo-parser. 
                        // let's parse the head of the demo-file to get which map the match is on!
                        // this is always the first step you need to do.
                        parser.ParseHeader();

                        // Getting the tickrate, which we use to limit the amount of data to roughly half-second intervals              
                        tickrate = parser.TickRate;
                        halfsecond = Math.Round(0.5 * tickrate);

                        bool error = false;

                        // Some files have bad headers. We can attempt to get around that using other values but it's highly likely that these data are also bad.
                        if (Double.IsNaN(tickrate))
                        {
                            error = true;
                            Console.WriteLine("=============ERROR=============");
                            try // Likely to get div by zero here
                            {
                                tickrate = parser.Header.PlaybackTicks / parser.Header.PlaybackTime;
                            }
                            catch (DivideByZeroException)
                            {
                                // Go to the next file - don't want to generate empty files.
                                Console.WriteLine("=============ERROR=============");
                                baddemos = baddemos + "," + fileName;
                                continue;
                            }
 
                        }

                        // In case it doesn't give a div by zero, we still check for NaN and skip
                        if (Double.IsNaN(tickrate))
                        {
                            Console.WriteLine("=============ERROR=============");
                            baddemos = baddemos + "," + fileName;
                            continue;
                        }

                        if (error)
                        {
                            Console.WriteLine("=============FIXED=============");
                            Console.WriteLine(tickrate);
                        }

                        // Got a good tickrate.
                        // Check for match start signal.

                        parser.MatchStarted += (sender, e) =>
                        {
                            hasMatchStartSignal = true;
                        };

                        parser.ParseToEnd();
                    }

                    // Okay. If we are still here, we are ready to collect data.
                    // Grab the external id from the filename
                    string[] splitfilename = fileName.Split('\\');
                    string matchcode = splitfilename[splitfilename.Length - 1].Split('_')[0];

                    Console.WriteLine(tickrate);

                    // Open everything again.
                    using (var fileStream = File.OpenRead(fileName))
                    {
                        Console.WriteLine("Parsing demo...");

                        using (var parser = new DemoParser(fileStream))
                        {

                            parser.ParseHeader();

                            // Might want to know cs vs de later but just using short names for now
                            string fullmap = parser.Map;
                            string map = fullmap.Split('_')[1];

                            // And now, generate the filenames of the resulting files
                            // Need to include map because matches can have multiple maps

                            string path;

                            if (args.Length > 1)
                            {
                                path = args[1];
                            }
                            else
                            {
                                path = args[0];
                            }

                            string outputFileNamePlayerData = path + "\\" + matchcode + "_" + map + "_playerdata.csv";
                            string outputFileNameNades = path + "\\" + matchcode + "_" + map + "_nadedata.csv";
                            string outputFileNameGameData = path + "\\" + matchcode + "_" + map + "_gamedata.csv";
                            string outputFileNameMatchInfo = path + "\\" + matchcode + "_" + map + "_matchinfo.csv"; //maybe put steamids/playernames in here

                            // and open it.
                            var outputStreamPlayerData = new StreamWriter(outputFileNamePlayerData);
                            var outputStreamNades = new StreamWriter(outputFileNameNades);
                            var outputStreamGameData = new StreamWriter(outputFileNameGameData);
                            var outputStreamMatchInfo = new StreamWriter(outputFileNameMatchInfo);

                            // And write a header so you know what is what in the resulting file
                            outputStreamPlayerData.WriteLine(GenerateCSVHeader()); // This was modified from statistics generator so I just used his method.
                            outputStreamNades.WriteLine(string.Format("Tick,Time,Round,CTScore,TScore,Thrower,Type,XPos,YPos,ZPos"));
                            outputStreamGameData.WriteLine(string.Format("Tick,Time,Round,CTScore,TScore,Reason"));
                            outputStreamMatchInfo.WriteLine(string.Format("Match Code,Map,Avg Rank,Team 1,Team 2"));

                            // Generating the analysis data. 
                            // Let's just declare some stuff we need to remember
                            bool hasMatchStarted = false;
                            bool hasRoundStarted = false;
                            bool hasMatchPrinted = false;
                            string CTTeamName = "Error";
                            string TTeamName = "Error";
                            List<Player> ingame = new List<Player>();

                            // If there is no match start signal, we begin right away.
                            if (!hasMatchStartSignal)
                            {
                                hasMatchStarted = true;
                                Console.WriteLine("Match start event not found. Trying to parse assuming match has already started...");

                                // Try to print/record the information that's include in match start parser
                                Console.WriteLine("{0}   Participants: {1}  vs  {2} ", matchcode, parser.CTClanName, parser.TClanName);

                                // Sometimes this info gets lost somewhere, so we store it locally.
                                CTTeamName = parser.CTClanName;
                                TTeamName = parser.TClanName;
                                ingame.AddRange(parser.PlayingParticipants);
                            }

                            // Since most of the parsing is done via "Events" in CS:GO, we need to use them. 
                            // So you bind to events in C# as well. 
                            // AFTER we have bound the events, we start the parser!

                            // Might be worthwhile trying to prevent multiple starts. I think this causes some issues in pistol round data (i.e., end of warmup is sometimes lumped into knife/pistol rounds)
                            parser.MatchStarted += (sender, e) =>
                            {
                                hasMatchStarted = true;
                                
                                // Pro games frequently start and restart several times before actually going
                                // This is just to clean up the console log.
                                if (!hasMatchPrinted)
                                {
                                    hasMatchPrinted = true;
                                    //Okay let's output who's really in this game!
                                    Console.WriteLine("Match parsing started...");
                                    Console.WriteLine("{0}   Participants: {1}  vs  {2} ", matchcode, parser.CTClanName, parser.TClanName);
                                }

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

                            // Only collect data if it's a half second interval
                            if (tick % halfsecond == 0 && hasRoundStarted)
                                {
                                    float time = tick * parser.TickTime;
                                    foreach (var player in parser.PlayingParticipants)
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

                                        // Extra equipment is stored in one cell so that csv rows have the same length
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

                            // Nades are recorded as events so we catch them regardless of tick time
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

                            //int thrower = e.ThrownBy.EntityID; //from the class "/// This currently *doesn't* contain who it threw since this is for some weird reason not networked"

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

                            parser.BombPlanted += (sender, e) => // Will have to get position from previous tick - just use posiiton that has a player with C4 as the active weapon
                            {
                                if (!hasMatchStarted)
                                    return;

                                int tick = parser.CurrentTick;
                                float time = tick * parser.TickTime;

                                int CTScore = parser.CTScore;
                                int TScore = parser.TScore;
                                int Round = CTScore + TScore + 1;

                                string StrTick = tick.ToString();

                            // Zeros are for position so these rows are the same length as other nades
                            // Changed thrownby to 99 - python will want an INT in that column.
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

                            // Now let's parse the demo!
                            // Unfortunately the header sometimes doesn't register the tick rate correctly, resulting in a System.IO.EndOfStreamException
                            // tickrate is NaN in that case so hopefully we just avoid parsing altogether above
                            try
                            {
                                Console.WriteLine("Trying to parse...");
                                parser.ParseToEnd();
                            }
                            catch (System.IO.EndOfStreamException)
                            {
                                Console.WriteLine(string.Format("Error in {0}. Parser attempted to exceed file length.", fileName));
                                baddemos = baddemos + "," + fileName;
                            }
                            catch (System.NullReferenceException)
                            {
                                Console.WriteLine(string.Format("Error in {0}. Parser attempted to exceed file length.", fileName));
                                baddemos = baddemos + "," + fileName;
                            }

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
                            outputStreamMatchInfo.WriteLine(string.Format("{0},{1},{2},{3},{4}", matchcode, map, avgrank, CTTeamName, TTeamName));

                            outputStreamPlayerData.Close();
                            outputStreamNades.Close();
                            outputStreamGameData.Close();
                            outputStreamMatchInfo.Close();
                            //outputStreamPlayerInfo.Close();

                        }

                    }

                    Console.WriteLine("=============Next=============");
                }

            }

            string[] badfiles = baddemos.Split(',');
            Console.WriteLine(string.Format("There were {0} bad files and {1} successfully processed files", badfiles.Length, files.Length - badfiles.Length));
        }

        private static void Print(string s)
        {
            Console.WriteLine(s);
        }


        static string GenerateCSVHeader() //need to modify for appropriate results 
        {
            return string.Format(
                "{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14}",
                "Tick Number (x2 in HLTV DEMOs)",
                "Time (s)",
                "Round",
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
            Console.WriteLine("Usage: {0} [--help] PathToDemoDirectory [PathToOutputDirectory]", fileName);
            Console.WriteLine("--help");
            Console.WriteLine("    Displays this help.");
            Console.WriteLine("PathToDemoDirector");
            Console.WriteLine("    Path to a directory containing demos to be parsed. The resulting csv files will have ");
            Console.WriteLine("    the match code and map name prepended and end with the contents of the file (player data, match data, etc.).");
            Console.WriteLine("[PathToOutputDirectory]");
            Console.WriteLine("    Optional argument to a directory for the output files. If no argument is provided,");
            Console.WriteLine("    the input directory will be used.");
        }

        static void PrintTickInfo(DemoParser parser, StreamWriter outputStream, string currentTick, float time, Team playerteam, int playerID, Vector playerpos, bool playerducking, int playerhp, int playerarmor, bool playerhelmet, bool playerdefuse, EquipmentElement playeractiveweapon, string allweapons)
        {
            outputStream.WriteLine(string.Format("{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12}", 
            currentTick,
            time,
            parser.CTScore + parser.TScore + 1, //Round number
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

