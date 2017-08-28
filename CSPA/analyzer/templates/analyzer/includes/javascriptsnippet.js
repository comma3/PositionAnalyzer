    {% load staticfiles %}
	
	<script type="text/javascript">

	// Stolen from https://stackoverflow.com/questions/42291370/csrf-token-ajax-based-post-in-a-django-project
    function getCookie(cname)
    {
        var name = cname + "=";
        var decodedCookie = decodeURIComponent(document.cookie);
        var ca = decodedCookie.split(';');
        for(var i = 0; i <ca.length; i++) {
            var c = ca[i];
            while (c.charAt(0) == ' ') {
                c = c.substring(1);
            }
            if (c.indexOf(name) == 0) {
                return c.substring(name.length, c.length);
            }
        }
        return "";
    }


	function runQuery()
	{
	    var goodInput = true;

	    var csrftoken = getCookie('csrftoken');
	    var xhr = new XMLHttpRequest();
	    //var url = "http://www.chu-bot.com/analyzer/query";
	    var url = "http://localhost:8080/analyzer/query";

	    if (document.getElementById("gameobjectsbox").value == ''){
	        alert("You have to have some game objects!!")
	        document.getElementById("query").disabled = false;
	        return
	    }
        objects = "gameobjects=" + document.getElementById("gameobjectsbox").value.replace(/\n/g,'_')
        map = "&map=" + document.getElementById("map").value;
        threshold = "&threshold=" + document.getElementById("threshold").value;
        if (threshold > 1)
        {
            alert("Threshold must be between 0 and 1. That is, it should be a decimal like 0.81");
            goodInput = false;
        }

        distance = "&distance=" + document.getElementById("distance").value;
		
		smokemin = "&smokemin=" + document.getElementById("smokemin").value;
		smokemax = "&smokemax=" + document.getElementById("smokemax").value;
		mollymin = "&mollymin=" + document.getElementById("mollymin").value;
		mollymax = "&mollymax=" + document.getElementById("mollymax").value;
		flashmin = "&flashmin=" + document.getElementById("flashmin").value;
		flashmax = "&flashmax=" + document.getElementById("flashmax").value;
		hemin = "&hemin=" + document.getElementById("hemin").value;
		hemax = "&hemax=" + document.getElementById("hemax").value;
		
	    params = objects + map + threshold + distance + smokemin + smokemax + mollymin + mollymax + flashmin + flashmax + hemin + hemax;
        xhr.open("POST", url, true);
	    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	    xhr.setRequestHeader("X-CSRFToken", csrftoken);
	    console.log(params)
	    if (goodInput)
	    {
	        document.getElementById("query").disabled = true;
            xhr.onreadystatechange = function()
            {
                if (xhr.readyState == 4)
                {
                    if (xhr.status == 200)
                    {
                        data = JSON.parse(xhr.response)['results'];
                        other = JSON.parse(xhr.response)
                        console.log(data);
                        console.log(other);

                        var tkills = 0;
                        var ctkills = 0;
                        var defuse = 0;
                        var bombed = 0;
                        var time = 0;

                        if (data.length < 1)
                        {
                            alert("No games found!");
                        }

                        for (i = 0; i < data.length; i++)
                        {
                            if (data[i][1] == 'TerroristWin'){
                                    tkills += 1;
                            } else if (data[i][1] == 'CTWin') {
                                    ctkills += 1;
                            } else if (data[i][1] == 'BombDefused') {
                                    defuse += 1;
                            } else if (data[i][1] == 'TargetBombed') {
                                    bombed += 1;
                            } else if (data[i][1] == 'TargetSaved') {
                                    time += 1;
                            }
                        };

                        // Not counting draws - need to figure out where they come from

                        var graphData = google.visualization.arrayToDataTable([
                          ['Winner', 'Percent'],
                          ['CTKills', ctkills],
                          ['Defuse', defuse],
                          ['Time',  time],
                          ['TKills', tkills],
                          ['Target Bombed', bombed],
                        ]);
                        drawChart(graphData);

                        data.sort().reverse();
                        var tableData = "<tr><th>Similarity</th><th>Win Reason</th><th>Score (T, CT)</th><th>Match Link </th></tr>";
                        var round;
                        var similarity ;
                        for (i = 0; i < data.length; i++)
                        {
                            if (data[i][1] != "Draw")
                            {
                                similarity = data[i][0]
                                tableData = tableData + '<tr><td>' + similarity.toFixed(3) + "</td><td>";
                                tableData = tableData + data[i][1] + "</td><td>";
                                tableData = tableData + data[i][3] + ", " + data[i][4] + "</td><td>";
                                round = parseInt(data[i][3]) + parseInt(data[i][4]) + 1;
                                tableData = tableData + "<a href=https://www.hltv.org" + data[i][2] + " target='_blank'> Round " + round + "</a></td></tr>";
                            }
                        }
                        document.getElementById("gamedata").innerHTML = tableData;

                    } else {
                        alert("Server error!")
                    }
                    document.getElementById("query").disabled = false;
                }
            }
            xhr.send(params);
        }
    }

	<!-- Pie Chart Code -->	
	google.charts.load('current', {'packages':['corechart']});
	<!-- google.charts.setOnLoadCallback(drawChart); -->


	function drawChart(data) 
	{
		var chart = new google.visualization.PieChart(document.getElementById('piechart'));
		
		var options = {
		  title: 'Round Results',
		  backgroundColor: '#f6f6f6',
		  chartArea:{width:'100%',height:'100%'},
		  colors:['#2554C7','#002295','#00004F','#C79926','#947100']
		};

		chart.draw(data, options);
	}

	
	function setActive(newObject)
	{
		if (BOMBCOUNT == 1 && (newObject == "BombDown" || newObject == "BombPlanted")) 
		{
			alert("You already have a bomb somewhere!");
		} else if (newObject == "T" && TCOUNT > 5) {
			alert("Too many Ts!");
		} else if (newObject == "CT" && CTCOUNT > 5) {
			alert("Too many CTs!");
		} else {
			OBJECT = newObject;
		}
	}


	//Special case of set active
	function setDead(player)
	{
		if (player == "T" && TCOUNT >= 5)
		{
			alert("Too many Ts!");
		} else if (player == "CT" && CTCOUNT >= 5) {
			alert("Too many CTs!");
		} else if (player == "T") {
			TCOUNT += 1
			OBJECT = "null";
			GAMEOBJECTS.push(player + " - Dead");
			gameobjectsbox.value=GAMEOBJECTS.join("\n");
		} else if (player == "CT") {
			CTCOUNT += 1
			OBJECT = "null";
			GAMEOBJECTS.push(player + " - Dead");
			gameobjectsbox.value=GAMEOBJECTS.join("\n");
		}
	}


	function setObjectPosition(x, y, selectedObject)
	{
		if (selectedObject != null)
		{
			switch (selectedObject) 
			{
				case "BombDown" :
				case "BombPlanted" :
				<!-- Too many bombs is handled by setActive, so setting a bomb can't be done. Could probably be hacked but it will just give zero results in the query.-->
					BOMBCOUNT = BOMBCOUNT + 1;
					insertIcon(selectedObject);
					selectedObject = selectedObject.replace("BombDown", "Bomb Down").replace("BombPlanted", "Bomb Planted")
					break;
					
				case "Smoke" :
					SMOKECOUNT = SMOKECOUNT + 1;
					if (SMOKECOUNT > 10){alert("More than 10 Smokes?");}
					cursorX = cursorX - 15
					cursorY = cursorY - 15
					insertIcon(selectedObject);
					break;
				
				case "Flash" : 
					FLASHCOUNT = FLASHCOUNT + 1;
					if (FLASHCOUNT > 20){alert("More than 20 Flashes?");}
					cursorX = cursorX - 15
					cursorY = cursorY - 15
					insertIcon(selectedObject);
					break;
				
				case "HE" : 
					HECOUNT = HECOUNT + 1;
					if (HECOUNT > 10){alert("More than 10 HEs?");}
					cursorX = cursorX - 13
					cursorY = cursorY - 13
					insertIcon(selectedObject);
					break;
				
				case "Molly" : 
					MOLLYCOUNT = MOLLYCOUNT + 1;
					if (MOLLYCOUNT > 10){alert("More than 10 mollies?");}
					cursorX = cursorX - 15
					cursorY = cursorY - 20
					insertIcon(selectedObject);
					break;
				
				case "Decoy" : 
					DECOYCOUNT = DECOYCOUNT + 1;
					if (DECOYCOUNT > 10){alert("More than 10 Decoys? Bold strategy.");}
                    cursorX = cursorX - 15
					cursorY = cursorY - 20
					insertIcon(selectedObject);
					break;
				
				case "T" :
				    if (TCOUNT > 10){alert("More than 5 Terrorists?");}
					selectedObject = selectedObject + ' - ' + document.getElementById('weapon').value;
                    cursorX = cursorX - 8
					cursorY = cursorY - 8
					insertIcon(selectedObject);
					break;
					
				case "CT" :
				    if (CTCOUNT > 10){alert("More than 5 CounterTerrorists?");}
					selectedObject = selectedObject + ' - ' + document.getElementById('weapon').value;
					cursorX = cursorX - 8
					cursorY = cursorY - 8
					insertIcon(selectedObject);
					break;
					
				default :
					alert("You snuck a weird thing in!");
					break;
			}
				
			OBJECT = null;
			GAMEOBJECTS.push(selectedObject + ' - ' + x + ',' + y);
			gameobjectsbox.value=GAMEOBJECTS.join("\n");
		}
	}


	function insertIcon(selectedIcon) 
	{
		// The django server replaces all of the templating so we need to hard code the switch in JavaScript
		var newImage = document.createElement("img");
		newImage.setAttribute('id', 'icon');
		// Default settings, can be overridden in switch statement
		// Currently defaults to player icon size because there are many more weapons
		newImage.setAttribute('height', '15px');
		newImage.setAttribute('width', '15px');
		newImage.setAttribute('class', 'icon');
		switch (selectedIcon)
		{
			case "Smoke" :
				newImage.setAttribute('height', '30px');
				newImage.setAttribute('width', '30px');
				newImage.setAttribute('src', "{% static 'img/smoke.png' %}");
				break;
			case "Flash" :
				newImage.setAttribute('height', '30px');
				newImage.setAttribute('width', '30px');
				newImage.setAttribute('src', "{% static 'img/flash.png' %}")
				newImage.setAttribute('style', "opacity:0.6");
				break;
			case "Molly" :
				newImage.setAttribute('height', '30px');
				newImage.setAttribute('width', '30px');
				newImage.setAttribute('src', "{% static 'img/molly.png' %}");
				break;
			case "HE" :
				newImage.setAttribute('height', '30px');
				newImage.setAttribute('width', '30px');
				newImage.setAttribute('src', "{% static 'img/he.png' %}");
				break;
			case "Decoy" :
				newImage.setAttribute('height', '30px');
				newImage.setAttribute('width', '30px');
				newImage.setAttribute('src', "{% static 'img/decoy.png' %}");
				break;		
			case "BombDown" :
				newImage.setAttribute('src', "{% static 'img/bombdown.png' %}");
				break;
			case "BombPlanted" :
				newImage.setAttribute('src', "{% static 'img/bombplanted.png' %}");
				break;
			case "T - Any" :
				newImage.setAttribute('src', "{% static 'img/T - Any.png' %}");
				break;
			case "CT - Any" :
				newImage.setAttribute('src', "{% static 'img/CT - Any.png' %}");
				break;
			default :
				newImage.setAttribute('src', "{% static 'img/decoy.png' %}");
		}
		newImage.style.left = cursorX + "px";
		newImage.style.top = cursorY + "px";
		document.body.appendChild(newImage);
	}

	
	function clearGameObjects()
	{
		GAMEOBJECTS.length = 0;
		gameobjectsbox.value=GAMEOBJECTS.join("\n");
		
		TCOUNT = 0;
		CTCOUNT = 0;
		SMOKECOUNT = 0;
		FLASHCOUNT = 0;
		HECOUNT = 0;
		MOLLYCOUNT = 0;
		DECOYCOUNT = 0;
		BOMBCOUNT = 0;
		
		while (document.getElementById("icon"))
		{
			removeIcon("icon");
		}
	}


	function removeIcon(selectedIcon)
	{
		var icon = document.getElementById(selectedIcon);
		icon.parentNode.removeChild(icon);
	}


	function resetAll()
	{
		clearGameObjects();
		OBJECT = "null";			
		drawChart();
	}


    var cursorX;
	var cursorY;
	function checkCursor()
	{
		document.onmousemove = function(e)
		{
			cursorX = e.pageX;
			cursorY = e.pageY;
		}
	}
	setInterval("checkCursor()", 100);


	function get_position()
	{
		pos_x = event.offsetX?(event.offsetX):event.pageX-document.getElementById("minimap").offsetRight;
        pos_y = event.offsetY?(event.offsetY):event.pageY-document.getElementById("minimap").offsetTop;
        if (OBJECT == "null")
        {
            alert("No object selected!")
        }
        else
        {
            setObjectPosition(pos_x, pos_y, OBJECT);
        }
	}

	function showAdvanced()
	{
	    if {isAdvanced}{
	        document.getElementById("Advanced1").innerHTML = ''
	        document.getElementById("Advanced2").innerHTML = ''
	        isAdvanced = false;
	    } else {
	        document.getElementById("Advanced1").innerHTML = "<b>Similarity threshold:</b><input id='threshold' type='text' value='0.81' class='form-control input-sm'><b>Smoke minimum:</b><input id='smokemin' type='text' value='-8' class='form-control input-sm'><b>Molly minimum:</b><input id='mollymin' type='text' value='-4' class='form-control input-sm'><b>Flash minimum:</b><input id='flashmin' type='text' value='-2' class='form-control input-sm'><b>HE minimum:</b><input id='hemin' type='text' value='-2' class='form-control input-sm'>";
	        document.getElementById("Advanced2").innerHTML = "<b>Rank:</b><select id='rank' class='form-control input-sm'><option value='pro'>Pro</option><option value='all'>All</option><option value='allmm'>All MM</option><option value='global'>Global</option><option value='smfc'>SMFC</option><option value='eagle'>Eagle</option><option value='mgedmg'>MGE/DMG</option><option value='mg'>MG1/2</option><option value='gn34'>GN3/4</option><option value='gn12'>GN1/2</option><option value='s45'>Silver4/5</option><option value='s123'>ChuBot's Level</option></select><b>Distance tolerance:</b><input id='distance' type='text' value='400' class='form-control input-sm'><b>Smoke maximum:</b><input id='smokemax' type='text' value='0' class='form-control input-sm'><b>Molly maximum:</b><input id='mollymax' type='text' value='0' class='form-control input-sm'><b>Flash maximum:</b><input id='flashmax' type='text' value='1' class='form-control input-sm'><b>HE maximum:</b><input id='hemax' type='text' value='1' class='form-control input-sm'>";
            isAdvanced = true;
        }
	}


    var isAdvanced = false;
	var OBJECT = null;
	var GAMEOBJECTS = [];
	var SMOKECOUNT = 0;
	var FLASHCOUNT = 0;
	var HECOUNT = 0;
	var MOLLYCOUNT = 0;
	var DECOYCOUNT = 0;
	var BOMBCOUNT = 0;
	var	TCOUNT = 0;
	var	CTCOUNT = 0;

	document.getElementById("sidebartitle").innerHTML = "CSGO Position Analyzer";

</script>