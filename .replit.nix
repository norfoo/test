{ pkgs }: {
  deps = [
    pkgs.python310
    pkgs.streamlit
    pkgs.pandas
    pkgs.numpy
    pkgs.matplotlib
    pkgs.plotly
    pkgs.requests
    pkgs.google-generativeai
  ];
}