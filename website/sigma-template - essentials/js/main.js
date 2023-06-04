let sigInst, canvas, $GP


/** LOAD CONFIG **/
let config = {};

//For debug allow a config=file.json parameter to specify the config
function GetQueryStringParams(sParam,defaultVal) {
    let sPageURL = ""+window.location;//.search.substring(1);//This might be causing error in Safari?
    if (sPageURL.indexOf("?") === -1) return defaultVal;
    sPageURL=sPageURL.substr(sPageURL.indexOf("?")+1);    
    let sURLVariables = sPageURL.split('&');
    for (let i = 0; i < sURLVariables.length; i++) {
        let sParameterName = sURLVariables[i].split('=');
        if (sParameterName[0] === sParam) {
            return sParameterName[1];
        }
    }
    return defaultVal;
}

jQuery.getJSON(GetQueryStringParams("config","config.json"), function(data, textStatus, jqXHR) {
	config=data;
	
	if (config.type !== "network") {
		//bad config
		alert("Invalid configuration settings.")
		return;
	}
	
	//As soon as page is ready (and data ready) set up it
	$(document).ready(setupGUI(config));
});//End JSON Config load


// FUNCTION DECLARATIONS

Object.size = function(obj) {
    var size = 0, key;
    for (key in obj) {
        if (obj.hasOwnProperty(key)) size++;
    }
    return size;
};


/** HANDLE EDGE ATTR TOGGLE **/
function toggleEdgeAttrs(clicked){
    // Get nearest div.edge-attrs
    let connectionWrap = $(clicked).parent(".membership");
    let attrGroup = $(connectionWrap).children('.edge-attrs')[0];

    // Toggle show/hide
    $(attrGroup).toggle();

    // Move arrow
    if ($(attrGroup).is(":hidden")) {
        $(clicked).removeClass("fa-caret-down");
        $(clicked).addClass("fa-caret-right");
    } else {
        $(clicked).removeClass("fa-caret-right");
        $(clicked).addClass("fa-caret-down");
    }
}


/** INITIALIZE SIGMA **/

function initSigma(config) {
    const data = config.data;

    let drawProps, graphProps, mouseProps;
    if (config.sigma && config.sigma.drawingProperties)
		drawProps=config.sigma.drawingProperties;
	else
		drawProps={
        defaultLabelColor: "#000",
        defaultLabelSize: 14,
        defaultLabelBGColor: "#ddd",
        defaultHoverLabelBGColor: "#002147",
        defaultLabelHoverColor: "#fff",
        labelThreshold: 10,
        defaultEdgeType: "curve",
        hoverFontStyle: "bold",
        fontStyle: "bold",
        activeFontStyle: "bold"
    };



    if (config.sigma && config.sigma.graphProperties)	
    	graphProps=config.sigma.graphProperties;
    else
    	graphProps={
        minNodeSize: 1,
        maxNodeSize: 7,
        minEdgeSize: 0.2,
        maxEdgeSize: 0.5
    	};
	
	if (config.sigma && config.sigma.mouseProperties) 
		mouseProps=config.sigma.mouseProperties;
	else
		mouseProps={
        minRatio: 0.75, // How far can we zoom out?
        maxRatio: 20, // How far can we zoom in?
    	};

    let a = sigma.init(document.getElementById("sigma-canvas")).drawingProperties(drawProps).graphProperties(graphProps).mouseProperties(mouseProps);
    sigInst = a;
    a.active = !1;
    a.neighbors = {};
    a.detail = !1;

    init_color_mode(config); //NOTE


    let dataReady = function () {//This is called as soon as data is loaded
        a.clusters = {};

        a.iterNodes(
            function (b) { //This is where we populate the array used for the group select box

                // note: index may not be consistent for all nodes. Should calculate each time.
                // alert(JSON.stringify(b.attr.attributes[5].val));
                // alert(b.x);
                a.clusters[b.color] || (a.clusters[b.color] = []);
                a.clusters[b.color].push(b.id);//SAH: push id not label
            }
        );

        a.bind("upnodes", function (a) {
            nodeActive(a.content[0])
        });

        a.draw();
        configSigmaElements(config);
    }

    if (data.indexOf("gexf")>0 || data.indexOf("xml")>0)
        a.parseGexf(data,dataReady);
    else
	    a.parseJson(data,dataReady);
    gexf = sigmaInst = null;

}



/** INTERFACE **/

function setupGUI(config) {

	// Initialise main interface elements
    let logo = ""; // Logo elements
	if (config.logo.file) {

		logo = "<img src=\"" + config.logo.file +"\"";
		if (config.logo.text) logo+=" alt=\"" + config.logo.text + "\"";
		logo+=">";
	} else if (config.logo.text) {
		logo="<h1>"+config.logo.text+"</h1>";
	} else {
        $("#maintitle").hide();
    }
	if (config.logo.link) logo="<a href=\"" + config.logo.link + "\">"+logo+"</a>";
	$("#maintitle").html(logo);

	// #title
    $("#page-title").html(config.text.title);
	$("#title").html("<h2>"+config.text.title+"</h2>");

	// #titletext
	$("#titletext").html(config.text.intro);

	// More information
	if (config.text.more) {
		$("#description").html(config.text.more);
	} else {
		//hide more information link
		$("#moreinformation").hide();
	}
	// Citation
	if (config.text.citation) {
        $("#citation").html(config.text.citation);
    } else {

    }

	// Legend

	// Node
	if (config.legend.nodeLabel) {
		$(".node").next().html(config.legend.nodeLabel);
	} else {
		//hide more information link
		$(".node").hide();
	}
	// Edge
	if (config.legend.edgeLabel) {
		$(".edge").next().html(config.legend.edgeLabel);
	} else {
		//hide more information link
		$(".edge").hide();
	}
	// Colours (general)
	if (config.legend.colorLabel) {
		$(".colours").next().html(config.legend.colorLabel);
	} else {
		//hide gradient image
        $(".colours").hide();
	}
    // Color Key
    if (config.legend.colorKey) {
        for (const [color, label] of Object.entries(config.legend.colorKey)) {
            let dot_element = $("<dt></dt>").css('background-color', color);
            let label_element= $("<dd></dd>").text(label);
            $("#color-key").append(dot_element, label_element);
        }

    } else {
        //hide key section
        $("#color-key").hide();
    }
    // Node Size
    if (config.legend.nodeSize) {
        $(".node-size").css('background', null)
        $(".node-size").next().html(config.legend.nodeSize);
    } else {
        //hide more information link
        $(".node-size").hide();
    }


    $GP = {
		calculating: !1,
		showgroup: !1
	};
    $GP.intro = $("#intro");
    $GP.minifier = $GP.intro.find("#minifier");
    $GP.mini = $("#minify");
    $GP.info = $("#attributepane");
    $GP.info_donnees = $GP.info.find(".nodeattributes");
    $GP.info_name = $GP.info.find(".name");
    $GP.info_link = $GP.info.find(".link");
    $GP.info_data = $GP.info.find(".data");
    $GP.info_close = $GP.info.find(".returntext");
    $GP.info_close2 = $GP.info.find(".close");
    $GP.info_p = $GP.info.find(".p");
    $GP.info_close.click(nodeNormal);
    $GP.info_close2.click(nodeNormal);
    $GP.form = $("#mainpanel").find("form");
    $GP.search = new Search($GP.form.find("#search"));
    if (!config.features.search) {
		$("#search").hide();
	}
	if (!config.features.groupSelectorAttribute) {
		$("#attributeselect").hide();
	}
    $GP.cluster = new Cluster($GP.form.find("#attributeselect"));
    config.GP=$GP;
    initSigma(config);

}

function configSigmaElements(config) {
	$GP=config.GP;
    
    // Node hover behaviour
    if (config.features.hoverBehavior == "dim") {

		var greyColor = '#ccc';
		sigInst.bind('overnodes',function(event){
		var nodes = event.content;
		var neighbors = {};
		sigInst.iterEdges(function(e){
		if(nodes.indexOf(e.source)<0 && nodes.indexOf(e.target)<0){
			if(!e.attr['grey']){
				e.attr['true_color'] = e.color;
				e.color = greyColor;
				e.attr['grey'] = 1;
			}
		}else{
			e.color = e.attr['grey'] ? e.attr['true_color'] : e.color;
			e.attr['grey'] = 0;

			neighbors[e.source] = 1;
			neighbors[e.target] = 1;
		}
		}).iterNodes(function(n){
			if(!neighbors[n.id]){
				if(!n.attr['grey']){
					n.attr['true_color'] = n.color;
					n.color = greyColor;
					n.attr['grey'] = 1;
				}
			}else{
				n.color = n.attr['grey'] ? n.attr['true_color'] : n.color;
				n.attr['grey'] = 0;
			}
		}).draw(2,2,2);
		}).bind('outnodes',function(){
		sigInst.iterEdges(function(e){
			e.color = e.attr['grey'] ? e.attr['true_color'] : e.color;
			e.attr['grey'] = 0;
		}).iterNodes(function(n){
			n.color = n.attr['grey'] ? n.attr['true_color'] : n.color;
			n.attr['grey'] = 0;
		}).draw(2,2,2);
		});

    } else if (config.features.hoverBehavior == "hide") {

		sigInst.bind('overnodes',function(event){
			var nodes = event.content;
			var neighbors = {};
		sigInst.iterEdges(function(e){
			if(nodes.indexOf(e.source)>=0 || nodes.indexOf(e.target)>=0){
		    	neighbors[e.source] = 1;
		    	neighbors[e.target] = 1;
		  	}
		}).iterNodes(function(n){
		  	if(!neighbors[n.id]){
		    	n.hidden = 1;
		  	}else{
		    	n.hidden = 0;
		  }
		}).draw(2,2,2);
		}).bind('outnodes',function(){
		sigInst.iterEdges(function(e){
		  	e.hidden = 0;
		}).iterNodes(function(n){
		  	n.hidden = 0;
		}).draw(2,2,2);
		});

    }
    $GP.bg = $(sigInst._core.domElements.bg);
    $GP.bg2 = $(sigInst._core.domElements.bg2);
    var a = [],
        group_color,x=1;
		for (group_color in sigInst.clusters) {
            let group_label = 'Group ' + (x++);
            // If there's a color key, use those labels for the group names
		    if (config.legend.colorKey && group_color in config.legend.colorKey) {
                group_label = config.legend.colorKey[group_color]
            }
            a.push('<div style="line-height:12px">' +
                '<a href="#' + group_color + '">' +
                    '<div style="width:40px;height:12px;border:1px solid #fff;background:' + group_color + ';display:inline-block"></div> ' +
                   group_label + ' (' + sigInst.clusters[group_color].length + ' members)' +
                '</a></div>');
        }
    //a.sort();
    $GP.cluster.content(a.join(""));
    group_color = {
        minWidth: 400,
        maxWidth: 800,
        maxHeight: 600
    };//        minHeight: 300,
    $("a.fb").fancybox(group_color);
    $("#zoom").find("div.z").each(function () {
        var a = $(this),
            b = a.attr("rel");
        a.click(function () {
			if (b == "center") {
				sigInst.position(0,0,1).draw();
			} else {
		        var a = sigInst._core;
	            sigInst.zoomTo(a.domElements.nodes.width / 2, a.domElements.nodes.height / 2, a.mousecaptor.ratio * ("in" == b ? 1.5 : 0.5));		
			}

        })
    });
    $GP.mini.click(function () {
        $GP.mini.hide();
        $GP.intro.show();
        $GP.minifier.show()
    });
    $GP.minifier.click(function () {
        $GP.intro.hide();
        $GP.minifier.hide();
        $GP.mini.show()
    });
    $GP.intro.find("#showGroups").click(function () {
        !0 == $GP.showgroup ? showGroups(!1) : showGroups(!0)
    });
    a = window.location.hash.substr(1);
    if (0 < a.length) switch (a) {
    case "Groups":
        showGroups(!0);
        break;
    case "information":
        $.fancybox.open($("#information"), group_color);
        break;
    default:
        $GP.search.exactMatch = !0, $GP.search.search(a)
		$GP.search.clean();
    }

}

function Search(a) {
    this.input = a.find("input[name=search]");
    this.state = a.find(".state");
    this.results = a.find(".results");
    this.exactMatch = !1;
    this.lastSearch = "";
    this.searching = !1;
    var b = this;
    this.input.focus(function () {
        var a = $(this);
        a.data("focus") || (a.data("focus", !0), a.removeClass("empty"));
        b.clean()
    });
    this.input.keydown(function (a) {
        if (13 == a.which) return b.state.addClass("searching"), b.search(b.input.val()), !1
    });
    this.state.click(function () {
        var a = b.input.val();
        b.searching && a == b.lastSearch ? b.close() : (b.state.addClass("searching"), b.search(a))
    });
    this.dom = a;
    this.close = function () {
        this.state.removeClass("searching");
        this.results.hide();
        this.searching = !1;
        this.input.val("");//SAH -- let's erase string when we close
        nodeNormal()
    };
    this.clean = function () {
        this.results.empty().hide();
        this.state.removeClass("searching");
        this.input.val("");
    };
    this.search = function (a) {
        var b = !1,
            c = [],
            b = this.exactMatch ? ("^" + a + "$").toLowerCase() : a.toLowerCase(),
            g = RegExp(b);
        this.exactMatch = !1;
        this.searching = !0;
        this.lastSearch = a;
        this.results.empty();
        if (2 >= a.length) this.results.html("<i>You must search for a name with a minimum of 3 letters.</i>");
        else {
            sigInst.iterNodes(function (a) {
                g.test(a.label.toLowerCase()) && c.push({
                    id: a.id,
                    name: a.label
                })
            });
            c.length ? (b = !0, nodeActive(c[0].id)) : b = showCluster(a);
            a = ["<b>Search Results: </b>"];
            if (1 < c.length) for (var d = 0, h = c.length; d < h; d++) a.push('<a href="#' + c[d].name + '" onclick="nodeActive(\'' + c[d].id + "')\">" + c[d].name + "</a>");
            0 == c.length && !b && a.push("<i>No results found.</i>");
            1 < a.length && this.results.html(a.join(""));
           }
        if(c.length!=1) this.results.show();
        if(c.length==1) this.results.hide();   
    }
}

function Cluster(a) {
    this.cluster = a;
    this.display = !1;
    this.list = this.cluster.find(".list");
    this.list.empty();
    this.select = this.cluster.find(".select");
    this.select.click(function () {
        $GP.cluster.toggle()
    });
    this.toggle = function () {
        this.display ? this.hide() : this.show()
    };
    this.content = function (a) {
        this.list.html(a);
        this.list.find("a").click(function () {
            var a = $(this).attr("href").substr(1);
            showCluster(a)
        })
    };
    this.hide = function () {
        this.display = !1;
        this.list.hide();
        this.select.removeClass("close")
    };
    this.show = function () {
        this.display = !0;
        this.list.show();
        this.select.addClass("close")
    }
}

function showGroups(a) {
    a ? ($GP.intro.find("#showGroups").text("Hide groups"), $GP.bg.show(), $GP.bg2.hide(), $GP.showgroup = !0) : ($GP.intro.find("#showGroups").text("View Groups"), $GP.bg.hide(), $GP.bg2.show(), $GP.showgroup = !1)
}

function nodeNormal() {
    !0 != $GP.calculating && !1 != sigInst.detail && (showGroups(!1), $GP.calculating = !0, sigInst.detail = !0, $GP.info.delay(400).animate({width:'hide'},350),$GP.cluster.hide(), sigInst.iterEdges(function (a) {
        a.attr.color = !1;
        a.hidden = !1
    }), sigInst.iterNodes(function (a) {
        a.hidden = !1;
        a.attr.color = !1;
        a.attr.lineWidth = !1;
        a.attr.size = !1
    }), sigInst.draw(2, 2, 2, 2), sigInst.neighbors = {}, sigInst.active = !1, $GP.calculating = !1, window.location.hash = "")
}

function nodeActive(a) {

	var groupByDirection=false;
	if (config.informationPanel.groupByEdgeDirection && config.informationPanel.groupByEdgeDirection==true)	groupByDirection=true;
	
    sigInst.neighbors = {};
    sigInst.detail = !0;
    var b = sigInst._core.graph.nodesIndex[a];
    showGroups(!1);
	var outgoing={},incoming={},mutual={};//SAH
    sigInst.iterEdges(function (b) {
        b.attr.lineWidth = !1;
        b.hidden = !0;

        b.attr.attributes["Edge Weight"] = b.size

        n={
            name: b.label,
            colour: b.color,
            edge_attr: b.attr.attributes, // NOTE: Added to include edge attributes downstream
        };
        
   	   if (a==b.source) outgoing[b.target]=n;		//SAH
	   else if (a==b.target) incoming[b.source]=n;		//SAH
       if (a == b.source || a == b.target) sigInst.neighbors[a == b.target ? b.source : b.target] = n;
       b.hidden = !1, b.attr.color = "rgba(0, 0, 0, 1)";
    });
    var f = [];
    sigInst.iterNodes(function (a) {
        a.hidden = !0;
        a.attr.lineWidth = !1;
        a.attr.color = a.color
    });
    
    if (groupByDirection) {
		//SAH - Compute intersection for mutual and remove these from incoming/outgoing
		for (e in outgoing) {
			//name=outgoing[e];
			if (e in incoming) {
				mutual[e]=outgoing[e];
				delete incoming[e];
				delete outgoing[e];
			}
		}
    }
    
    var createList=function(c) {
        var f = [];
    	var connections_list = [],
      	 	 //c = sigInst.neighbors,
       		 g;
    for (g in c) {
        var d = sigInst._core.graph.nodesIndex[g];
        d.hidden = !1;
        d.attr.lineWidth = !1;
        d.attr.color = c[g].colour;
        a != g && connections_list.push({
            id: g,
            name: d.label,
            group: (c[g].name)? c[g].name:"",
            colour: c[g].colour,
            edge_attr: c[g].edge_attr //NOTE: Added to include edge attrs downstream
        })
    }
    connections_list.sort(function (a, b) {
        var c = a.group.toLowerCase(),
            d = b.group.toLowerCase(),
            e = a.name.toLowerCase(),
            f = b.name.toLowerCase();
        return c != d ? c < d ? -1 : c > d ? 1 : 0 : e < f ? -1 : e > f ? 1 : 0
    });
    d = "";
		for (g in connections_list) {  // G = neighbor node name

			c = connections_list[g];  // Neighbor node


            //Note: Edge attr dropdown created here
            var edge_attr_tags = ""
            if (config.informationPanel.edgeAttributes) {
                var attrs_to_list = config.informationPanel.edgeAttributes;
                for (var i in attrs_to_list) {
                    let attribute = attrs_to_list[i]
                    if (attribute in c.edge_attr){
                        let attribute_value = c.edge_attr[attribute].toString()
                        if (!attribute_value){ attribute_value = "" }


                        // attribute_value = JSON.parse(attribute_value.replace("'", '"').replace("'", '"'));
                        attribute_value = JSON.parse(attribute_value.replace(/'|'|'/g, '"'))
                        let is_list = Array.isArray(attribute_value);
                        // if (attribute_value[0] === "[" && attribute_value[attribute_value.length - 1]==="]") {
                        //     is_list = true;
                        // }

                        if (is_list){
                            var list_attribute_string = "<div class='edge-attr-wrap'>" +
                                "<span class='edge-attr-label'>"+ attribute +": </span>" + "<ul class='edge-attr-value'>";

                            for (let i in attribute_value) {
                                let display_value = attribute_value[i].replace("'", "").replace("'", "")
                                list_attribute_string += "<li>" + display_value + "</li>";
                            }
                            list_attribute_string += "</ul></div>";
                            edge_attr_tags += list_attribute_string;

                        } else {
                            edge_attr_tags += "<div class='edge-attr-wrap'>" +
                                "<span class='edge-attr-label'>"+ attribute +": </span>" +
                                "<span class='edge-attr-value'>"+ c.edge_attr[attribute] +"</span>" +
                                "</div>"
                        }

                    }
                }


                f.push('<li class="membership">' +
                    '<i class="edge-attr-toggle fa-solid fa-caret-right" onclick="toggleEdgeAttrs(this)"></i>' +
                    '<a class="connection-label" href="#' + c.name + '" ' +
                    'onmouseover="sigInst._core.plotter.drawHoverNode(sigInst._core.graph.nodesIndex[\'' + c.id + '\'])\" ' +
                    'onclick=\"nodeActive(\'' + c.id + '\')" onmouseout="sigInst.refresh()">' + c.name + "</a> " +
                    '<div class="edge-attrs" hidden>' + edge_attr_tags +'</div>' +
                    "</li>");
            } else {

                /*if (c.group != d) {
                    d = c.group;
                    f.push('<li class="cf" rel="' + c.color + '"><div class=""></div><div class="">' + d + "</div></li>");
                }*/

                f.push('<li class="membership">' +
                    '<a class="connection-label" href="#' + c.name + '" ' +
                    'onmouseover="sigInst._core.plotter.drawHoverNode(sigInst._core.graph.nodesIndex[\'' + c.id + '\'])\" ' +
                    'onclick=\"nodeActive(\'' + c.id + '\')" onmouseout="sigInst.refresh()">' + c.name + "</a> " +
                    '<div class="edge-attrs" hidden>' + edge_attr_tags + '</div>' +
                    "</li>");
            }
		}
		return f;
	}

	/*console.log("mutual:");
	console.log(mutual);
	console.log("incoming:");
	console.log(incoming);
	console.log("outgoing:");
	console.log(outgoing);*/
	
	
	var f=[];
	
	//console.log("neighbors:");
	//console.log(sigInst.neighbors);

	if (groupByDirection) {
		size=Object.size(mutual);
		f.push("<h2>Mututal (" + size + ")</h2>");
		(size>0)? f=f.concat(createList(mutual)) : f.push("No mutual links<br>");
		size=Object.size(incoming);
		f.push("<h2>Incoming (" + size + ")</h2>");
		(size>0)? f=f.concat(createList(incoming)) : f.push("No incoming links<br>");
		size=Object.size(outgoing);
		f.push("<h2>Outgoing (" + size + ")</h2>");
		(size>0)? f=f.concat(createList(outgoing)) : f.push("No outgoing links<br>");
	} else {
		f=f.concat(createList(sigInst.neighbors));
	}
	//b is object of active node -- SAH
    b.hidden = !1;
    b.attr.color = b.color;
    b.attr.lineWidth = 6;
    b.attr.strokeStyle = "#000000";
    sigInst.draw(2, 2, 2, 2);

    $GP.info_link.find("ul").html(f.join(""));
    $GP.info_link.find("li").each(function () { // Connections table?
        var a = $(this),
            b = a.attr("rel");
        $(this).innerText = "Test"
    });
    f = b.attr;
    if (f.attributes) {
  		var image_attribute = false;
  		if (config.informationPanel.imageAttribute) {
  			image_attribute=config.informationPanel.imageAttribute;
  		}
        e = [];
        temp_array = [];
        g = 0;
        let allowed_attributes = config.informationPanel.nodeAttributes;
        if (!allowed_attributes){ allowed_attributes = Object.keys(f.attributes); }
        for (var attr_name in f.attributes) {
            var attr_value = f.attributes[attr_name],
                h = "";
			if (attr_name!=image_attribute) {
			    if (!allowed_attributes.includes(attr_name)){ continue; } // filter out attributes not in the config
                if (attr_value.includes("http://") || attr_value.includes("https://")) {
                    console.log("link");
                    h = '<span><strong>' + attr_name + ':</strong>' +
                        ' <a href="' + attr_value + '" target="_blank">' + attr_value + '</a></span><br/>'
                } else {
                    h = '<span><strong>' + attr_name + ':</strong> ' + attr_value + '</span><br/>'
                }
			}
            e.push(h)
        }

        if (image_attribute) {
        	$GP.info_name.html("<div><img src=" + f.attributes[image_attribute] + " style=\"vertical-align:middle\" /> <span onmouseover=\"sigInst._core.plotter.drawHoverNode(sigInst._core.graph.nodesIndex['" + b.id + '\'])" onmouseout="sigInst.refresh()">' + b.label + "</span></div>");
        } else {
        	$GP.info_name.html("<div><span onmouseover=\"sigInst._core.plotter.drawHoverNode(sigInst._core.graph.nodesIndex['" + b.id + '\'])" onmouseout="sigInst.refresh()">' + b.label + "</span></div>");
        }
        // Image field for attribute pane
        $GP.info_data.html(e.join("<br/>"))
    }
    $GP.info_data.show();
    $GP.info_p.html("Connections:");
    $GP.info.animate({width:'show'},350);
	$GP.info_donnees.hide();
	$GP.info_donnees.show();
    sigInst.active = a;
    window.location.hash = b.label;
}

function showCluster(a) {
    var b = sigInst.clusters[a];
    if (b && 0 < b.length) {
        showGroups(!1);
        sigInst.detail = !0;
        b.sort();
        sigInst.iterEdges(function (a) {
            a.hidden = !1;
            a.attr.lineWidth = !1;
            a.attr.color = !1
        });
        sigInst.iterNodes(function (a) {
            a.hidden = !0
        });
        for (var f = [], e = [], c = 0, g = b.length; c < g; c++) {
            var d = sigInst._core.graph.nodesIndex[b[c]];
            !0 == d.hidden && (e.push(b[c]), d.hidden = !1, d.attr.lineWidth = !1, d.attr.color = d.color, f.push('<li class="membership"><a href="#'+d.label+'" onmouseover="sigInst._core.plotter.drawHoverNode(sigInst._core.graph.nodesIndex[\'' + d.id + "'])\" onclick=\"nodeActive('" + d.id + '\')" onmouseout="sigInst.refresh()">' + d.label + "</a></li>"))
        }


        sigInst.clusters[a] = e;
        sigInst.draw(2, 2, 2, 2);
        $GP.info_name.html("<b>" + a + "</b>");
        $GP.info_data.hide();
        $GP.info_p.html("Group Members:");
        $GP.info_link.find("ul").html(f.join("")); // Add connections
        $GP.info.animate({width:'show'},350);
        $GP.search.clean();
		$GP.cluster.hide();
        return !0
    }
    return !1
}



/** DARKMODE **/
function dark_mode_toggle(){
    let current_mode = $("#darkmode-toggle").data("mode");

    if (current_mode === "light") {
        sigInst.drawingProperties({"defaultLabelColor": "#fff"});
        $("#sigma-canvas").css("background-color", "#1d1d1d");
        $("#darkmode-toggle").data("mode", "dark");
    } else {
        sigInst.drawingProperties({"defaultLabelColor": "#000"});
        $("#sigma-canvas").css("background-color", "#eee");
        $("#darkmode-toggle").data("mode", "light");
    }

}

function init_color_mode(config){
    // INIT DARK MODE
    let default_mode = config.sigma.drawingProperties.defaultMode;
    if (default_mode === "dark") {
        sigInst.drawingProperties({"defaultLabelColor": "#fff"});
        $("#sigma-canvas").css("background-color", "#1d1d1d");
        $("#darkmode-toggle").data("mode", "dark");
    } else {
        sigInst.drawingProperties({"defaultLabelColor": "#000"});
        $("#sigma-canvas").css("background-color", "#eee");
        $("#darkmode-toggle").data("mode", "light");
    }
}