import { Classes } from "@blueprintjs/core";
import React from "react";
import * as globals from "../../globals";

const MIN_WIDTH = 150;
const MIN_HEIGHT=100;
class Layout extends React.Component {
  /*
    Layout - this react component contains all the layout style and logic for the application once it has loaded.

    The layout is based on CSS grid: the left and right sidebars have fixed widths, the graph in the middle takes the
    remaining space.

    Note, the renderGraph child is a function rather than a fully-instantiated element because the middle pane of the
    app is dynamically-sized. It must have access to the containing viewport in order to know how large the graph
    should be.
  */
  constructor (props) {
    super(props);
    this.state = {
      dragging: false,
      separatorXPosition: undefined,
      leftWidth: globals.leftSidebarWidth,
      dragging2: false,
      separatorXPosition2: undefined,
      rightWidth: globals.rightSidebarWidth,  
      dragging3:true,
      separatorYPosition3:undefined,  
      upperRightHeight:globals.upperRightSidebarHeight,
      
    }
  }


  componentDidMount() {
    /*
      This is a bit of a hack. In order for the graph to size correctly, it needs to know the size of the parent
      viewport. Unfortunately, it can only do this once the parent div has been rendered, so we need to render twice.
    */
    this.forceUpdate();
    document.addEventListener("mousemove", this.onMouseMove);
    document.addEventListener("mouseup", this.onMouseUp);    
  }
  componentWillUnmount() {
    document.removeEventListener("mousemove", this.onMouseMove);
    document.removeEventListener("mouseup", this.onMouseUp);    
  }

  onMouseDown = (e) => {
    this.setState({
      separatorXPosition: e.clientX,
      dragging: true
    })
  };

  onMouseDown2 = (e) => {
    this.setState({
      separatorXPosition2: e.clientX,
      dragging2: true
    })
  };

  onMouseDown3 = (e) => {
    this.setState({
      separatorYPosition3: e.clientY,
      dragging3: true
    })
  };
  
  

  onMove = (clientX, clientY) => {
    const { dragging, leftWidth, separatorXPosition,
            dragging2, rightWidth, separatorXPosition2, 
            dragging3, upperRightHeight, separatorYPosition3} = this.state;

    if (dragging && leftWidth && separatorXPosition) {
      const newLeftWidth = leftWidth + clientX - separatorXPosition;

      if (newLeftWidth < MIN_WIDTH) {
        this.setState({
          leftWidth: MIN_WIDTH,
          separatorXPosition: clientX
        })
        return;
      }
      this.setState({
        leftWidth: newLeftWidth,
        separatorXPosition: clientX
      })
    }

    if (dragging2 && rightWidth && separatorXPosition2) {
      const newRightWidth = rightWidth - clientX + separatorXPosition2;

      if (newRightWidth < MIN_WIDTH) {
        this.setState({
          rightWidth: MIN_WIDTH,
          separatorXPosition2: clientX
        })
        return;
      }
      this.setState({
        rightWidth: newRightWidth,
        separatorXPosition2: clientX
      })
    }  

    if (dragging3 && upperRightHeight && separatorYPosition3) {
      const newUpperRightHeight = upperRightHeight - clientY + separatorYPosition3;

      if (newUpperRightHeight < MIN_HEIGHT) {
        this.setState({
          upperRightHeight: MIN_HEIGHT,
          separatorYPosition3: clientY
        })
        return;
      }
      this.setState({
        upperRightHeight: newUpperRightHeight,
        separatorYPosition3: clientY
      })
    }
  };

  onMouseMove = (e) => {
    const { dragging, leftWidth, separatorXPosition, separatorYPosition3,upperRightHeight,
      dragging3, dragging2, rightWidth, separatorXPosition2 } = this.state;    
    if ((dragging2 && rightWidth && separatorXPosition2) || (dragging && leftWidth && separatorXPosition)|| (dragging3 && upperRightHeight && separatorYPosition3)) {
      e.preventDefault();
    }
    this.onMove(e.clientX, e.clientY);
  };
  

  onMouseUp = () => {
    const { dragging, dragging2, dragging3 } = this.state;
    if (dragging||dragging2||dragging3)
    {
      window.dispatchEvent(new Event('resize'));  //I want the resize to also trigger when I change a component size
      this.setState({
        dragging: false,
        dragging2: false,
        dragging3: false,
      })
    }  
  };
  


  render() {
    const { children } = this.props;
    const { leftWidth, rightWidth, upperRightHeight } = this.state;
    const [leftSidebar, renderGraph, rightSidebar, renderGraph2] = children;
    //console.log(window.innerWidth - leftWidth - rightWidth)
    return (
      <div
        className={Classes.POPOVER_DISMISS}
        style={{
          display: "grid",
          gridTemplateColumns: `
          [left-sidebar-start] ${leftWidth + 1}px
          [left-sidebar-end divider-start] 10px
          [divider-end graph-start] auto
          [graph-end divider2-start] 10px
          [divider2-end right-sidebar-start]          
          ${
            rightWidth + 1
          }px [right-sidebar-end]
        `,
          gridTemplateRows: `[top] auto 
          [divider3-start] 10px
          [divider3-end right-canvas-bot-sidebar-start]  ${upperRightHeight + 1}px
          [bottom]`,
          gridTemplateAreas: "left-sidebar | divider | graph | divider2 | right-sidebar",
          columnGap: "0px",
          justifyItems: "stretch",
          alignItems: "stretch",
          height: "inherit",
          width: "inherit",
          position: "relative",
          top: 0,
          left: 0,
          minWidth: "1240px",
        }}
      >
        <div
          style={{
            gridArea: "top / left-sidebar-start / bottom / left-sidebar-end",
            position: "relative",
            height: "inherit",
            overflowX: "auto",
            overflowY: "auto"         
          }}
        >
          {React.cloneElement(leftSidebar,{...leftSidebar.props, leftWidth})}
        </div>
        <div
          style={{
              gridArea: "top / divider-start / bottom / divider-end",
              cursor: "col-resize",
              alignSelf: "stretch",
              display: "flex",
              borderLeft: `1px solid ${globals.lightGrey}`,              
              alignItems: "center",
              zIndex: 0                
          }}
          onMouseDown={this.onMouseDown}
        />
        <div
          style={{
            zIndex: 0,
            gridArea: "top / graph-start / bottom / graph-end",
            position: "relative",
            height: "inherit",
          }}
          ref={(ref) => {
            this.viewportRef = ref;
          }}
        >
          {this.viewportRef ? renderGraph(this.viewportRef) : null}
        </div>
        <div
          style={{
              gridArea: "top / divider2-start / bottom / divider2-end",
              cursor: "col-resize",
              alignSelf: "stretch",
              display: "flex",
              alignItems: "center",
              borderRight: `1px solid ${globals.lightGrey}`,              
              zIndex: 0              
          }}
          onMouseDown={this.onMouseDown2}
        />        
        <div
          style={{
            gridArea: "top / right-sidebar-start / divider3-start / right-sidebar-end",
            position: "relative",
            height: "inherit",
            overflowY: "auto",
            overflowX: "auto"
          }}
        >
          {React.cloneElement(rightSidebar,{...rightSidebar.props, rightWidth})}
          
          
        </div>

        <div
          style={{
              gridArea: "divider3-start / right-sidebar-start / divider3-end / right-sidebar-end",
              cursor: "row-resize",
              alignSelf: "stretch",
              display: "flex",
              alignItems: "center",
              borderTop: `1px solid ${globals.lightGrey}`,              
              zIndex: 0              
          }}
          onMouseDown={this.onMouseDown3}
        />   

        <div
          style={{
            zIndex: 0,
            gridArea: "right-canvas-bot-sidebar-start / right-sidebar-start / bottom / right-sidebar-end",
            position: "relative",
            height: "inherit",
          }}
          ref={(ref) => {
            this.viewportRef2 = ref;
          }}
        >
          {this.viewportRef2 ? renderGraph2(this.viewportRef2) : null}
        </div>
      </div>
    );
  }
}

export default Layout;
