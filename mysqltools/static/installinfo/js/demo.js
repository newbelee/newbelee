jsPlumb.ready(function () {

    var instance = jsPlumb.getInstance({
        // default drag options
        DragOptions: { cursor: 'pointer', zIndex: 2000 },
        // the overlays to decorate each connection with.  note that the label overlay uses a function to generate the label text; in this
        // case it returns the 'labelText' member that we set on each connection in the 'init' method below.
        ConnectionOverlays: [
            [ "Arrow", { location: 1 } ],
            [ "Label", {
                location: 0.5,
                id: "label",    
                //cssClass: "aLabel"
                cssClass: "aLabel1"
            }]
        ],
        Container: "flowchart-demo"
    });

    var basicType = {
        connector: "StateMachine",
        paintStyle: { strokeStyle: "red", lineWidth: 4 },
        hoverPaintStyle: { strokeStyle: "blue" },
        overlays: [
            "Arrow"
        ]
    };
    instance.registerConnectionType("basic", basicType);

    // this is the paint style for the connecting lines..
    var connectorPaintStyle = {
            //这是连接线条的粗细
            lineWidth: 3,  
            strokeStyle: "#61B7CF",
            joinstyle: "round",
            outlineColor: "white",
            outlineWidth: 2
        },
    // .. and this is the hover style.
        connectorHoverStyle = {
            lineWidth: 3,
            strokeStyle: "#216477",
            outlineWidth: 2,
            outlineColor: "white"
        },
        endpointHoverStyle = {
            fillStyle: "#216477",
            strokeStyle: "#216477"
        },
    // the definition of source endpoints (the small blue ones)
        sourceEndpoint = {
            endpoint: "Dot",
            paintStyle: {
                strokeStyle: "#7AB02C",
                fillStyle: "transparent",
                radius: 0.001,
                lineWidth: 0.001
            },
            isSource: true,
            connector: [ "Flowchart", { stub: [40, 60], gap: 10, cornerRadius: 5, alwaysRespectStubs: true } ],
            connectorStyle: connectorPaintStyle,
            hoverPaintStyle: endpointHoverStyle,
            connectorHoverStyle: connectorHoverStyle,
            dragOptions: {},
            overlays: [
                [ "Label", {
                    location: [0.5, 1.5],
                 //   label: "Drag",
                    label: "",
                    cssClass: "endpointSourceLabel"
                } ]
            ]
        },
    // the definition of target endpoints (will appear when the user drags a connection)
        targetEndpoint = {
            endpoint: "Dot",
            paintStyle: { fillStyle: "#7AB02C", radius: 0.001 },
            hoverPaintStyle: endpointHoverStyle,
            maxConnections: -1,
            dropOptions: { hoverClass: "hover", activeClass: "active" },
            isTarget: true,
            overlays: [
          //      [ "Label", { location: [0.5, -0.5], label: "Drop", cssClass: "endpointTargetLabel" } ]
                  [ "Label", { location: [0.5, -0.5], label: "", cssClass: "endpointTargetLabel" } ]    
            ]
        },
       init = function (connection) {
           // connection.getOverlay("label").setLabel(connection.sourceId.substring(15) + "-" + connection.targetId.substring(15));
        };

    var _addEndpoints = function (toId, sourceAnchors, targetAnchors) {
        for (var i = 0; i < sourceAnchors.length; i++) {
            var sourceUUID = toId + sourceAnchors[i];
            instance.addEndpoint("flowchart" + toId, sourceEndpoint, {
                anchor: sourceAnchors[i], uuid: sourceUUID
            });
        }
        for (var j = 0; j < targetAnchors.length; j++) {
            var targetUUID = toId + targetAnchors[j];
            instance.addEndpoint("flowchart" + toId, targetEndpoint, { anchor: targetAnchors[j], uuid: targetUUID });
        }
    };

    // suspend drawing and initialise.
    instance.batch(function () {

        //_addEndpoints("Window4", ["TopCenter", "BottomCenter"], ["LeftMiddle", "RightMiddle"]);
        _addEndpoints("Window1", ["RightMiddle"], ["LeftMiddle", ]);
        _addEndpoints("Window2", ["RightMiddle"], ["LeftMiddle", ]);
        _addEndpoints("Window3", ["RightMiddle"], ["LeftMiddle", ]);
        _addEndpoints("Window4", ["RightMiddle"], ["LeftMiddle", ]);
        _addEndpoints("Window5", ["LeftMiddle"], ["RightMiddle", ]);
        _addEndpoints("Window6", ["LeftMiddle"], ["RightMiddle", ]);
        _addEndpoints("Window7", ["LeftMiddle"], ["RightMiddle", ]);
        _addEndpoints("Window8", ["LeftMiddle"], ["RightMiddle", ]);
		_addEndpoints("Window100", ["RightMiddle"], ["LeftMiddle", ]);
		_addEndpoints("Window101", ["LeftMiddle"], ["RightMiddle", ]); 
		_addEndpoints("Window9", ["RightMiddle"], ["LeftMiddle", ]);       
 
        // listen for new connections; initialise them the same way we initialise the connections at startup.
        instance.bind("connection", function (connInfo, originalEvent) {
            init(connInfo.connection);
        });

        // make all the window divs draggable
        instance.draggable(jsPlumb.getSelector(".flowchart-demo .window"), { grid: [1, 1] });
        // THIS DEMO ONLY USES getSelector FOR CONVENIENCE. Use your library's appropriate selector
        // method, or document.querySelectorAll:
        //jsPlumb.draggable(document.querySelectorAll(".window"), { grid: [20, 20] });

        // connect a few up
        instance.connect({uuids: ["Window100RightMiddle", "Window1LeftMiddle"], editable: true});
		instance.connect({uuids: ["Window1RightMiddle", "Window9LeftMiddle"], editable: true});
        instance.connect({uuids: ["Window9RightMiddle", "Window2LeftMiddle"], editable: true});
		instance.connect({uuids: ["Window2RightMiddle", "Window3LeftMiddle"], editable: true});
        instance.connect({uuids: ["Window3RightMiddle", "Window4LeftMiddle"], editable: true});
        instance.connect({uuids: ["Window4RightMiddle", "Window5RightMiddle"], editable: true});
        instance.connect({uuids: ["Window5LeftMiddle", "Window6RightMiddle"], editable: true});
        instance.connect({uuids: ["Window6LeftMiddle", "Window7RightMiddle"], editable: true});
        instance.connect({uuids: ["Window7LeftMiddle", "Window8RightMiddle"], editable: true});
        instance.connect({uuids: ["Window8LeftMiddle", "Window101RightMiddle"], editable: true});

        //instance.connect({uuids: ["Window3RightMiddle", "Window2RightMiddle"], editable: true});
        //instance.connect({uuids: ["Window4BottomCenter", "Window1TopCenter"], editable: true});
       // instance.connect({uuids: ["Window3BottomCenter", "Window1BottomCenter"], editable: true});
        //

        //
        // listen for clicks on connections, and offer to delete connections on click.
        //
        instance.bind("click", function (conn, originalEvent) {
           // if (confirm("Delete connection from " + conn.sourceId + " to " + conn.targetId + "?"))
             //   instance.detach(conn);
            conn.toggleType("basic");
        });

        instance.bind("connectionDrag", function (connection) {
            console.log("connection " + connection.id + " is being dragged. suspendedElement is ", connection.suspendedElement, " of type ", connection.suspendedElementType);
        });

        instance.bind("connectionDragStop", function (connection) {
            console.log("connection " + connection.id + " was dragged");
        });

        instance.bind("connectionMoved", function (params) {
            console.log("connection " + params.connection.id + " was moved");
        });
    });

    jsPlumb.fire("jsPlumbDemoLoaded", instance);

});
