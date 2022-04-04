// Bloodrooster javascript for index.html


// globals
var nodes = null;
var edges = null;
var network = null;

// draw a vis.js network given json formatted string containing nodes and edges
function draw(jsonstr='') {
    nodes = [];
    edges = [];

    node_font = { size: 12, color: "white", face: "arial" }
    edge_font = { size: 12, color: "white", face: "arial" }

    console.log(jsonstr.length);
    console.log(jsonstr);

    if (jsonstr.length > 0) {
        jsonobj = JSON.parse(jsonstr);
        if (jsonobj != null) {
            // translate nodes json into vis compatible format
            Object.entries(jsonobj.nodes).forEach((entry) => {
                const [key, value] = entry;
                id = value.id;
                label = value.name;
                group = value.group;
                image = getImagePathForNode(value.type);
                nodes.push({
                    id: id,
                    label: label,
                    title: id,
                    group: group,
                    font: node_font,
                    image: image,
                    shape: "image"
                });
            });

            // translate edges json into vis compatible format
            Object.entries(jsonobj.edges).forEach((entry) => {
                const [key, value] = entry;
                id = value.id;
                from = value.from;
                to = value.to;
                label = value.label;
                edges.push({from: from, to: to, label: label, font: edge_font});
            });
        }
    }

    var data = {
        nodes: nodes,
        edges: edges,
    };

    // reset config element
    var y = document.getElementById("config");
    y.innerHTML = "";

    ////////////////////
    // create a network
    ////////////////////

    var container = document.getElementById("mynetwork");

    var options = {
      physics: {
        stabilization: false,
        hierarchicalRepulsion: {
          avoidOverlap: 1,
        },
      },
      layout: {
        hierarchical: {
            direction: "LR",
            sortMethod: "directed",
        },
      },
      configure: {
        filter: function (option, path) {
          if (path.indexOf("physics") !== -1) {
            return true;
          }
          if (path.indexOf("smooth") !== -1 || option === "smooth") {
            return true;
          }
          return false;
        },
        container: document.getElementById("config"),
      },
    };

    network = new vis.Network(container, data, options);

    //////////////////
    // event handlers
    /////////////////

    network.on("doubleClick", function (params) {
        var test = network.getSelectedNodes()

        if (test.length > 0) {
            console.log(test[0])
            // ajax past to /extended_info to request new graph data
            $.ajax({
                type:'POST',
                url:'/extended_info',
                data: test[0],
                success:function(text) {
                    var y = document.getElementById("extended_info");
                    y.innerHTML = text;
                }
            });
        }
    });

    network.on("oncontext", function (params) {
        params.event.preventDefault();
        $(".custom-menu").finish().toggle(100);
        $(".custom-menu").css({
            top: params.event.pageY + "px",
            left: params.event.pageX + "px"
        });
    });
}

function getImagePathForNode(nodetype='') {
    var computer_path = "static/images/computer.png";
    var user_path = "static/images/user.png";
    var group_path = "static/images/group.png";
    var ou_path = 'static/images/organizational.png';
    var group_policy_path = 'static/images/group_policy.png'
    var container_path = 'static/images/container.png';
    var user_list_path = 'static/images/user_list.png';
    var unknown_path = "static/images/unknown.png";

    image = unknown_path;

    switch(nodetype) {
        case "computer":
            image = computer_path;
            break;
        case "user":
            image = user_path;
            break;
        case "group":
            image = group_path;
            break;
        case "ou":
            image = ou_path;
            break;
        case "group_policy":
            image = group_policy_path;
            break;
        case "container":
            image = container_path;
            break;
        case "user_list":
            image = user_list_path;
            break;
        default:
            image = unknown_path;
            break;
    }
    return image;
}

function draw_inputs() {
    var submit_type = $('#submit_type').val()

    // hide all input divs
    document.getElementById("src_form").style.display = "none";
    document.getElementById("dst_form").style.display = "none";

    switch(submit_type) {
        case "shortest_path_src":
            document.getElementById("src_form").style.display = "block";
            break;
        case "shortest_path_dst":
            document.getElementById("dst_form").style.display = "block";
            break;
        case "shortest_path_src_dst":
            document.getElementById("src_form").style.display = "block";
            document.getElementById("dst_form").style.display = "block";
            break;
        default:
            break;
    }
}

// toggle showing the vis.js config options
function showAdvanced() {
    var x = document.getElementById("config");
    var y = document.getElementById("showadvancedbutton");
    if (x.style.display === "none") {
        x.style.display = "block";
        y.innerHTML = "Graph Advanced Settings ↓";
    } else {
        x.style.display = "none";
        y.innerHTML = "Graph Advanced Settings →";
    }
}

// toggle showing the egde toggle options
function showEdgeToggle() {
    var x = document.getElementById("edgetoggle");
    var y = document.getElementById("edgetogglebutton");
    if (x.style.display === "none") {
        x.style.display = "block";
        y.innerHTML = "Edge toggle ↓";
    } else {
        x.style.display = "none";
        y.innerHTML = "Edge toggle →";
    }
}

// draw the spinning loading icon
function showLoading() {
    var y = document.getElementById("mynetwork");
    y.innerHTML = '<div id="loader"></div>';
}

// submit_button handler
function submit_clicked() {
    //e.preventDefault();
    showLoading();

    // package all fields into json object
    var data = {
        'src': $('#src').val(),  // source name
        'dst': $('#dst').val(),  // destination name
        'edges': create_edge_list(),  // list of enabled edges
        'submit_type': $('#submit_type').val()  // function type
    };

    // ajax past to /graph_update to request new graph data
    $.ajax({
        type:'POST',
        url:'/graph_update',
        data: JSON.stringify(data),
        processData: false,
        contentType: "application/json; charset=UTF-8",
        success:function(text) {
            draw(text);  // redraw the network with new data
        }
    });
}

// custom context menu item click handler
$(".custom-menu li").click(function() {
    switch($(this).attr("data-action")) {
        case "info":
            break;
    }
    // Hide it AFTER the action was triggered
    $(".custom-menu").hide(100);
});

// create list of strings for enabled edges
function create_edge_list() {
    var edge_list = []

    var ele = document.getElementById("member_check").checked
    if (ele === true) {
        edge_list.push('member');
    }

    ele = document.getElementById("WriteOwner_check").checked
    if (ele === true) {
        edge_list.push('WriteOwner');
    }

    ele = document.getElementById("Owns_check").checked
    if (ele === true) {
        edge_list.push('Owns');
    }

    ele = document.getElementById("GenericWrite_check").checked
    if (ele === true) {
        edge_list.push('GenericWrite');
    }

    ele = document.getElementById("GenericAll_check").checked
    if (ele === true) {
        edge_list.push('GenericAll');
    }

    ele = document.getElementById("AllExtendedRights_check").checked
    if (ele === true) {
        edge_list.push('AllExtendedRights');
    }

    ele = document.getElementById("AddKeyCredentialLink_check").checked
    if (ele === true) {
        edge_list.push('AddKeyCredentialLink');
    }

    ele = document.getElementById("GetChanges_check").checked
    if (ele === true) {
        edge_list.push('GetChanges');
    }

    ele = document.getElementById("GetChangesAll_check").checked
    if (ele === true) {
        edge_list.push('GetChangesAll');
    }

    ele = document.getElementById("AddMember_check").checked
    if (ele === true) {
        edge_list.push('AddMember');
    }

    ele = document.getElementById("All_check").checked
    if (ele === true) {
        edge_list.push('All');
    }

    ele = document.getElementById("Owner_check").checked
    if (ele === true) {
        edge_list.push('Owner');
    }

    ele = document.getElementById("ReadGMSAPassword_check").checked
    if (ele === true) {
        edge_list.push('ReadGMSAPassword');
    }

    ele = document.getElementById("User-Force-Change-Password_check").checked
    if (ele === true) {
        edge_list.push('User-Force-Change-Password');
    }

    ele = document.getElementById("WriteDacl_check").checked
    if (ele === true) {
        edge_list.push('WriteDacl');
    }

    ele = document.getElementById("sqladmin_check").checked
    if (ele === true) {
        edge_list.push('sqladmin');
    }

    return edge_list
}

function autocomplete(inp) {
    var currentFocus;

    /* create input event list */
    inp.addEventListener("input", function(e) {
        var a, b, i, val = this.value;

        /* close any already open lists of autocompleted values */
        closeAllLists();

        if (!val) { return false;}
        currentFocus = -1;

        /* create a DIV element that will contain the items (values): */
        a = document.createElement("DIV");
        a.setAttribute("id", this.id + "autocomplete-list");
        a.setAttribute("class", "autocomplete-items");

        /*append the DIV element as a child of the autocomplete container:*/
        this.parentNode.appendChild(a);

        // get autocomplete list using ajax POST
        $.ajax({
            type:'POST',
            url:'/autocomplete',
            data: val,
            success:function(ret) {
                var arr = JSON.parse(ret);

                /* for each item in the array... */
                for (i = 0; i < arr.length; i++) {
                    /* create a DIV element for each matching element: */
                    b = document.createElement("DIV");

                    /* make the matching letters bold: */
                    b.innerHTML = "<strong>" + arr[i].substr(0, val.length) + "</strong>";
                    b.innerHTML += arr[i].substr(val.length);

                    /* insert a input field that will hold the current array item's value: */
                    b.innerHTML += "<input type='hidden' value='" + arr[i] + "'>";

                    /* execute a function when someone clicks on the item value (DIV element): */
                    b.addEventListener("click", function(e) {
                        /* insert the value for the autocomplete text field: */
                        inp.value = this.getElementsByTagName("input")[0].value;

                        /* close the list of autocompleted values, (or any other open lists of autocompleted values */
                        closeAllLists();
                    });
                    a.appendChild(b);
                }
            }
        });
    });

    /* execute a function presses a key on the keyboard: */
    inp.addEventListener("keydown", function(e) {
        var x = document.getElementById(this.id + "autocomplete-list");
        if (x) x = x.getElementsByTagName("div");
        if (e.keyCode == 40) {
            /* If the arrow DOWN key is pressed, increase the currentFocus variable: */
            currentFocus++;

            /* and and make the current item more visible: */
            addActive(x);
        } else if (e.keyCode == 38) { //up
            /*If the arrow UP key is pressed,
            decrease the currentFocus variable:*/
            currentFocus--;
            /*and and make the current item more visible:*/
            addActive(x);
        } else if (e.keyCode == 13) {
        /*If the ENTER key is pressed, prevent the form from being submitted,*/
        e.preventDefault();
            if (currentFocus > -1) {
                /*and simulate a click on the "active" item:*/
                if (x) x[currentFocus].click();
            }
        }
    });

  function addActive(x) {
    /*a function to classify an item as "active":*/
    if (!x) return false;
    /*start by removing the "active" class on all items:*/
    removeActive(x);
    if (currentFocus >= x.length) currentFocus = 0;
    if (currentFocus < 0) currentFocus = (x.length - 1);
    /*add class "autocomplete-active":*/
    x[currentFocus].classList.add("autocomplete-active");
  }

  function removeActive(x) {
    /*a function to remove the "active" class from all autocomplete items:*/
    for (var i = 0; i < x.length; i++) {
      x[i].classList.remove("autocomplete-active");
    }
  }

  function closeAllLists(elmnt) {
    /*close all autocomplete lists in the document,
    except the one passed as an argument:*/
    var x = document.getElementsByClassName("autocomplete-items");
    for (var i = 0; i < x.length; i++) {
      if (elmnt != x[i] && elmnt != inp) {
        x[i].parentNode.removeChild(x[i]);
      }
    }
  }

  /* execute a function when someone clicks in the document: */
  document.addEventListener("click", function (e) {
      closeAllLists(e.target);
  });
}

function test_clicked() {
    console.log('ADFHJDHF');

    $.ajax({
        type:'POST',
        url:'/autocomplete',
        data: document.getElementById("myText").value,
        success:function(text) {
            //draw(text);  // redraw the network with new data
        }
    });

    //network.body.data.nodes.add({ id: 72, label: "one"});
    //network.body.data.nodes.add({ id: 73, label: "two"});
    //network.body.data.nodes.add({ id: 74, label: "three"});
    //network.body.data.nodes.add({ id: 75, label: "four"});

    //network.body.data.edges.add({from: 72, to: 73});
    //network.body.data.edges.add({from: 73, to: 74});
    //network.body.data.edges.add({from: 74, to: 75});
    //network.body.data.edges.add({from: 75, to: "S-1-5-21-3937601378-3721788405-2067139823-1834"});
}