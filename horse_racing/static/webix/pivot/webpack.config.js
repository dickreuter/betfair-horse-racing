var path = require('path');
var webpack = require('webpack');

var ExtractTextPlugin = require("extract-text-webpack-plugin");
var LiveReloadPlugin = require('webpack-livereload-plugin');

var config = {
  entry: './sources/pivot.js',
  output: {
    path: path.join(__dirname, 'codebase'),
    publicPath:"/codebase/",
    filename: 'pivot.js'
  },
  devtool:"source-map",
  module: {
    loaders: [
      {
        test: path.join(__dirname, 'sources'),
        loader: 'babel'
      },
      {
      	test: /\.(png|jpg|gif)$/,
      	loader: 'url?limit=25000'
      },
      {
        test: /\.less$/,
        loader: ExtractTextPlugin.extract("css!less")
      },
      { 
        test: /\.(eot|woff|woff2|ttf|svg)/,
        loader: 'file?name=fonts/[name].[ext]'
      }
    ]
  },
  resolve: {
    extensions: ['', '.js'],
    modulesDirectories: ["./sources", "node_modules", "bower_components"]
  },
  plugins: [
    new ExtractTextPlugin("./pivot.css"),
    new LiveReloadPlugin(),
    new webpack.optimize.UglifyJsPlugin({
        compress: {
            warnings: false
        }
    })
  ]
};

module.exports = config;