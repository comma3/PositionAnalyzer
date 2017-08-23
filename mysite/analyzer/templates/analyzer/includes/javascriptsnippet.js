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
	    document.getElementById("query").disabled = true;
	    var csrftoken = getCookie('csrftoken');
	    var xhr = new XMLHttpRequest();
	    var url = "http://localhost:8080/analyzer/query";

	    if (document.getElementById("gameobjectsbox").value == ''){
	        alert("You have to have some game objects!!")
	        document.getElementById("query").disabled = false;
	        return
	    }
        objects = "gameobjects=" + document.getElementById("gameobjectsbox").value.replace(/\n/g,'_')
        map = "&map=" + document.getElementById("map").value;
        threshold = "&threshold=" + document.getElementById("threshold").value;
        distance = "&distance=" + document.getElementById("distance").value;
	    params = objects + map + threshold + distance
        xhr.open("POST", url, true);
	    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	    xhr.setRequestHeader("X-CSRFToken", csrftoken);
	    console.log(params)
	    xhr.onreadystatechange = function()
	    {
            if (xhr.readyState == 4) {
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

                    for (i = 0; i < data.length; i++) {
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
                    for (i = 0; i < data.length; i++) {
                        if (data[i][1] != "Draw")
                        {
                            similarity = data[i][0]*100
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
		if (player == "T" && TCOUNT >= 5) {
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
					cursorX = cursorX - 7
					cursorY = cursorY - 7
					insertIcon(selectedObject);
					break;
				
				case "Flash" : 
					FLASHCOUNT = FLASHCOUNT + 1;
					if (FLASHCOUNT > 20){alert("More than 20 Flashes?");}
					cursorX = cursorX - 7
					cursorY = cursorY - 7
					insertIcon(selectedObject);
					break;
				
				case "HE" : 
					HECOUNT = HECOUNT + 1;
					if (HECOUNT > 10){alert("More than 10 HEs?");}
					cursorX = cursorX - 3
					cursorY = cursorY - 3
					insertIcon(selectedObject);
					break;
				
				case "Molly" : 
					MOLLYCOUNT = MOLLYCOUNT + 1;
					if (MOLLYCOUNT > 10){alert("More than 10 mollies?");}
					cursorX = cursorX - 5
					cursorY = cursorY - 10
					insertIcon(selectedObject);
					break;
				
				case "Decoy" : 
					DECOYCOUNT = DECOYCOUNT + 1;
					if (DECOYCOUNT > 10){alert("More than 10 Decoys? Bold strategy.");}
					insertIcon(selectedObject);
					break;
				
				case "T" :
					selectedObject = selectedObject + ' - ' + document.getElementById('weapon').value;
					insertIcon(selectedObject);
					break;
					
				case "CT" : 
					selectedObject = selectedObject + ' - ' + document.getElementById('weapon').value;
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
				newImage.setAttribute('src', "{% static 'img/Smoke.png' %}");
				break;
			case "Flash" :
				newImage.setAttribute('height', '30px');
				newImage.setAttribute('width', '30px');
				newImage.setAttribute('src', "{% static 'img/Flash.png' %}")
				newImage.setAttribute('style', "opacity:0.6");
				break;
			case "Molly" :
				newImage.setAttribute('height', '30px');
				newImage.setAttribute('width', '30px');
				newImage.setAttribute('src', "{% static 'img/Molly.png' %}");
				break;
			case "HE" :
				newImage.setAttribute('height', '30px');
				newImage.setAttribute('width', '30px');
				newImage.setAttribute('src', "{% static 'img/HE.png' %}");
				break;
			case "Decoy" :
				newImage.setAttribute('height', '30px');
				newImage.setAttribute('width', '30px');
				newImage.setAttribute('src', "{% static 'img/Decoy.png' %}");
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
				newImage.setAttribute('src', "{% static 'img/Decoy.png' %}");
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
		document.onmousemove = function(e){
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