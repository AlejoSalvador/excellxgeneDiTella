import React from "react";
import Helmet from "react-helmet";
import { connect } from "react-redux";
import Container from "./framework/container";
import Layout from "./framework/layout";
import LeftSideBar from "./leftSidebar";
import RightSideBar from "./rightSidebar";
import Legend from "./continuousLegend";
import Graph from "./graph/graph";
import MenuBar from "./menubar";
import Autosave from "./autosave";
import Embedding from "./embedding";
import TermsOfServicePrompt from "./termsPrompt";
import { GlobalHotkeys } from "./hotkeys";
import Sankey from "./sankey";
import actions from "../actions";
import ImageViewer from "./graph/imageViewer";

@connect((state) => ({
  loading: state.controls.loading,
  error: state.controls.error,
  graphRenderCounter: state.controls.graphRenderCounter,
  sankey: state.layoutChoice.sankey,
}))
class App extends React.Component {
  componentDidMount() {
    const { dispatch } = this.props;
    /* listen for url changes, fire one when we start the app up */
    window.addEventListener("popstate", this._onURLChanged);
    this._onURLChanged();
    dispatch(actions.doInitialDataLoad(window.location.search))
    this.forceUpdate();
  }

  _onURLChanged() {
    const { dispatch } = this.props;

    dispatch({ type: "url changed", url: document.location.href });
  }

  render() {
    const { dispatch, sankey } = this.props;
    const { loading, error, graphRenderCounter } = this.props;

    return (
      <Container>        
        <Helmet title="cellxgene" />
        {loading ? (
          <div
            style={{
              position: "fixed",
              fontWeight: 500,
              top: window.innerHeight / 2,
              left: window.innerWidth / 2 - 50,
            }}
          >
            loading cellxgene
          </div>
        ) : null}
        {error ? (
          <div
            style={{
              position: "fixed",
              fontWeight: 500,
              top: window.innerHeight / 2,
              left: window.innerWidth / 2 - 50,
            }}
          >
            error loading cellxgene
          </div>
        ) : null}
        {loading || error ? null : (
          <Layout>
            <LeftSideBar />
            {(viewportRef) => {
              return (
              <>
              
                <GlobalHotkeys dispatch={dispatch} />
                <MenuBar />
                <Embedding />
                <Autosave />
                <TermsOfServicePrompt />
                <Legend viewportRef={viewportRef} />
                {sankey && <div style={{
                    zIndex: 0,
                    gridArea: "top / graph-start / bottom / graph-end",
                    position: "relative",
                    height: "inherit",
                    overflowY: "auto"
                  }}> <Sankey viewportRef={viewportRef} sankeyWidth={viewportRef?.clientWidth}/></div>}
                <div style={{
                    zIndex: 0,
                    gridArea: "top / graph-start / bottom / graph-end",
                    position: "relative",
                    height: sankey ? "0px" : "inherit",
                    overflowX: "auto"
                  }}>
                <Graph sankeyPlotMode={sankey} key={graphRenderCounter} graphWidth={viewportRef?.clientWidth} viewportRef={viewportRef} />
                </div>
              </>
            )}}
            <RightSideBar />

            {(viewportRef) => {
              return (
              <>
                <Legend viewportRef={viewportRef} />
                <div style={{
                    zIndex: 0,
                    gridArea: "top / right-sidebar-start / bottom / right-sidebar-end",
                    position: "relative",
                    height: sankey ? "0px" : "inherit",
                    overflowX: "auto"
                  }}>
                <ImageViewer sankeyPlotMode={sankey} key={graphRenderCounter} graphWidth={viewportRef?.clientWidth} viewportRef={viewportRef} />
                </div>
              </>
            )}}
          </Layout>
        )}
      </Container>
    );
  }
}

export default App;
