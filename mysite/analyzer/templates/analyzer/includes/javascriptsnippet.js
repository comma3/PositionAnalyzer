    {% load staticfiles %}
	
	<script type="text/javascript">
	
	function errorTest()
	{
		if ({{BadSearch}}) {
			resetAll();
		} else if ({{Error}}) {
			alert("Something went wrong!");
			resetAll();
		} else if ({{NoGames}}) {
			alert("No games matched your search. Consider removing some limited factors.");
			resetAll();			
		}
		
		document.getElementById("sidebartitle").innerHTML = "CSGO Position Analyzer";
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
			GAMEOBJECTS.push(player + " - Dead - Still dead");
			gameobjectsbox.value=GAMEOBJECTS.join("\n");
		} else if (player == "CT") {
			CTCOUNT += 1
			OBJECT = "null";
			GAMEOBJECTS.push(player + " - Dead - Still dead");
			gameobjectsbox.value=GAMEOBJECTS.join("\n");
		}
	}
	
	function setObjectPosition(positionID, selectedObject)
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
			GAMEOBJECTS.push(selectedObject + ' - ' + positionID);
			gameobjectsbox.value=GAMEOBJECTS.join("\n");
		}
	}
	
	//TODO: Fix this!
	function insertIcon(selectedIcon) 
	{
		// myImage : ID of image on which to place new image
		var image = document.getElementById("maplistener");
		
		// The django server replaces all of the templating so we need to hard code the switch in JavaScript
		var newImage = document.createElement("img");
		newImage.setAttribute('id', 'icon');
		//default settings, can be overridden in switch statement
		// Currently defaults to player icon size because there are many more weapons
		newImage.setAttribute('height', '15px');
		newImage.setAttribute('width', '15px');
		newImage.setAttribute('class', 'icon');
		console.log(selectedIcon);
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
		drawResults();
	}
	
	
	function drawResults()
	{
		var data = google.visualization.arrayToDataTable([
          ['Winner', 'Percent'],
          ['CTKills', {{CTKill}}],
          ['Defuse', {{Defuse}}],
          ['Time',  {{Time}}],
          ['TKills', {{TKill}}],
          ['Target Bombed', {{TargetBombed}}],
        ]);
		
		drawChart(data);
	}
	
	var OBJECT = null;
	var GAMEOBJECTS = [];
	var SMOKECOUNT = 0;
	var FLASHCOUNT = 0;
	var HECOUNT = 0;
	var MOLLYCOUNT = 0;
	var DECOYCOUNT = 0;
	var BOMBCOUNT = 0;
	var cursorX;
	var cursorY;

	function checkCursor() {
		document.onmousemove = function(e){
			cursorX = e.pageX;
			cursorY = e.pageY;
		}
	}

	setInterval("checkCursor()", 100);
	
	

</script>