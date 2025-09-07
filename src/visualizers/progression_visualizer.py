"""
Progression Visualization Module

This module creates interactive visualizations for chess progression analysis,
showing how playing style and capabilities have evolved over time.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class ProgressionVisualizer:
    """Creates interactive visualizations for chess progression analysis."""
    
    def __init__(self):
        """Initialize the progression visualizer."""
        self.color_scheme = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#2ca02c',
            'warning': '#d62728',
            'info': '#9467bd',
            'light': '#17becf',
            'dark': '#8c564b'
        }
    
    def create_rating_progression_chart(self, progression_data: Dict) -> go.Figure:
        """
        Create an interactive rating progression chart.
        
        Args:
            progression_data: Results from ProgressionAnalyzer
            
        Returns:
            Plotly figure showing rating progression over time
        """
        rating_data = progression_data.get('rating_progression', {})
        if not rating_data or not rating_data.get('rating_history'):
            return self._create_no_data_figure("No rating data available")
        
        df = pd.DataFrame(rating_data['rating_history'])
        
        fig = go.Figure()
        
        # Main rating line
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['rating'],
            mode='lines+markers',
            name='Rating',
            line=dict(color=self.color_scheme['primary'], width=2),
            marker=dict(size=4),
            hovertemplate='<b>Date:</b> %{x}<br><b>Rating:</b> %{y}<br><extra></extra>'
        ))
        
        # Moving averages
        if 'rating_ma_10' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['rating_ma_10'],
                mode='lines',
                name='10-Game Average',
                line=dict(color=self.color_scheme['secondary'], width=1, dash='dash'),
                hovertemplate='<b>10-Game Avg:</b> %{y:.0f}<br><extra></extra>'
            ))
        
        if 'rating_ma_30' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['rating_ma_30'],
                mode='lines',
                name='30-Game Average',
                line=dict(color=self.color_scheme['success'], width=1, dash='dot'),
                hovertemplate='<b>30-Game Avg:</b> %{y:.0f}<br><extra></extra>'
            ))
        
        # Peak rating line
        peak_rating = rating_data.get('peak_rating', 0)
        if peak_rating > 0:
            fig.add_hline(
                y=peak_rating,
                line_dash="dash",
                line_color=self.color_scheme['warning'],
                annotation_text=f"Peak: {peak_rating}",
                annotation_position="top right"
            )
        
        fig.update_layout(
            title={
                'text': f"Rating Progression ({rating_data.get('trend_direction', 'stable').title()})",
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title="Date",
            yaxis_title="Rating",
            hovermode='x unified',
            showlegend=True,
            height=500
        )
        
        return fig
    
    def create_accuracy_trends_chart(self, progression_data: Dict) -> go.Figure:
        """Create accuracy trends visualization."""
        accuracy_data = progression_data.get('accuracy_trends', {})
        if not accuracy_data:
            return self._create_no_data_figure("No accuracy data available")
        
        # Create sample data for visualization (in real implementation, this would come from the data)
        # For now, we'll create a placeholder chart
        fig = go.Figure()
        
        # Add accuracy trend information as text
        current_acc = accuracy_data.get('current_accuracy', 0)
        starting_acc = accuracy_data.get('starting_accuracy', 0)
        improvement = accuracy_data.get('accuracy_improvement', 0)
        
        fig.add_annotation(
            x=0.5, y=0.7,
            text=f"Current Accuracy: {current_acc:.1f}%",
            showarrow=False,
            font=dict(size=16),
            xref="paper", yref="paper"
        )
        
        fig.add_annotation(
            x=0.5, y=0.5,
            text=f"Starting Accuracy: {starting_acc:.1f}%",
            showarrow=False,
            font=dict(size=16),
            xref="paper", yref="paper"
        )
        
        fig.add_annotation(
            x=0.5, y=0.3,
            text=f"Improvement: {improvement:+.1f}%",
            showarrow=False,
            font=dict(size=16, color=self.color_scheme['success'] if improvement > 0 else self.color_scheme['warning']),
            xref="paper", yref="paper"
        )
        
        fig.update_layout(
            title="Accuracy Trends",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=400
        )
        
        return fig
    
    def create_tactical_improvement_chart(self, progression_data: Dict) -> go.Figure:
        """Create tactical improvement visualization."""
        tactical_data = progression_data.get('tactical_improvement', {})
        if not tactical_data:
            return self._create_no_data_figure("No tactical data available")
        
        # Create a bar chart showing tactical improvements
        categories = ['Error Rate', 'Missed Tactics', 'Tactical Score']
        improvements = [
            tactical_data.get('error_rate_improvement', 0),
            tactical_data.get('tactical_vision_improvement', 0),
            tactical_data.get('best_tactical_game', 0) - tactical_data.get('worst_tactical_game', 0)
        ]
        
        colors = [self.color_scheme['success'] if x > 0 else self.color_scheme['warning'] for x in improvements]
        
        fig = go.Figure(data=[
            go.Bar(
                x=categories,
                y=improvements,
                marker_color=colors,
                text=[f"{x:+.1f}" for x in improvements],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="Tactical Improvement Metrics",
            yaxis_title="Improvement",
            height=400
        )
        
        return fig
    
    def create_opening_evolution_chart(self, progression_data: Dict) -> go.Figure:
        """Create opening evolution visualization."""
        opening_data = progression_data.get('opening_evolution', {})
        if not opening_data:
            return self._create_no_data_figure("No opening evolution data available")
        
        # Create a summary chart
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Repertoire Size', 'New Openings', 'Performance Changes', 'Summary'),
            specs=[[{"type": "indicator"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "table"}]]
        )
        
        # Repertoire size indicator
        repertoire_expansion = opening_data.get('repertoire_expansion', 0)
        fig.add_trace(
            go.Indicator(
                mode="number+delta",
                value=opening_data.get('recent_diversity', 0),
                delta={'reference': opening_data.get('early_diversity', 0)},
                title={"text": "Current Repertoire Size"},
                domain={'x': [0, 1], 'y': [0, 1]}
            ),
            row=1, col=1
        )
        
        # New openings bar
        new_openings = opening_data.get('new_openings', [])
        if new_openings:
            fig.add_trace(
                go.Bar(
                    x=new_openings[:5],  # Top 5 new openings
                    y=[1] * len(new_openings[:5]),
                    name="New Openings",
                    marker_color=self.color_scheme['success']
                ),
                row=1, col=2
            )
        
        # Performance changes
        performance_changes = opening_data.get('performance_changes', {})
        if performance_changes:
            openings = list(performance_changes.keys())[:5]
            changes = [performance_changes[op] for op in openings]
            colors = [self.color_scheme['success'] if x > 0 else self.color_scheme['warning'] for x in changes]
            
            fig.add_trace(
                go.Bar(
                    x=openings,
                    y=changes,
                    marker_color=colors,
                    name="Performance Change (%)"
                ),
                row=2, col=1
            )
        
        fig.update_layout(height=600, title_text="Opening Evolution Analysis")
        
        return fig
    
    def create_consistency_metrics_chart(self, progression_data: Dict) -> go.Figure:
        """Create consistency metrics visualization."""
        consistency_data = progression_data.get('consistency_metrics', {})
        if not consistency_data:
            return self._create_no_data_figure("No consistency data available")
        
        # Create a radar chart for consistency metrics
        categories = ['Score Consistency', 'Accuracy Consistency', 'Performance Stability']
        values = [
            consistency_data.get('score_consistency', 0),
            consistency_data.get('accuracy_consistency', 0),
            100 - (consistency_data.get('performance_volatility', 0) * 100)  # Convert to consistency score
        ]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Consistency Metrics',
            line_color=self.color_scheme['primary']
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title="Performance Consistency",
            height=500
        )
        
        return fig
    
    def create_comprehensive_dashboard(self, progression_data: Dict) -> go.Figure:
        """Create a comprehensive dashboard with multiple progression metrics."""
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Rating Progression', 'Accuracy Trends',
                'Tactical Improvement', 'Opening Evolution',
                'Consistency Metrics', 'Summary Insights'
            ),
            specs=[
                [{"secondary_y": False}, {"secondary_y": False}],
                [{"secondary_y": False}, {"secondary_y": False}],
                [{"type": "scatterpolar"}, {"type": "table"}]
            ],
            vertical_spacing=0.08
        )
        
        # Rating progression (simplified)
        rating_data = progression_data.get('rating_progression', {})
        if rating_data:
            current_rating = rating_data.get('current_rating', 0)
            starting_rating = rating_data.get('starting_rating', 0)
            peak_rating = rating_data.get('peak_rating', 0)
            
            fig.add_trace(
                go.Bar(
                    x=['Starting', 'Current', 'Peak'],
                    y=[starting_rating, current_rating, peak_rating],
                    marker_color=[self.color_scheme['info'], self.color_scheme['primary'], self.color_scheme['success']],
                    name="Rating"
                ),
                row=1, col=1
            )
        
        # Accuracy trends
        accuracy_data = progression_data.get('accuracy_trends', {})
        if accuracy_data:
            fig.add_trace(
                go.Bar(
                    x=['Starting', 'Current', 'Best'],
                    y=[
                        accuracy_data.get('starting_accuracy', 0),
                        accuracy_data.get('current_accuracy', 0),
                        accuracy_data.get('best_accuracy', 0)
                    ],
                    marker_color=[self.color_scheme['info'], self.color_scheme['primary'], self.color_scheme['success']],
                    name="Accuracy"
                ),
                row=1, col=2
            )
        
        # Tactical improvement
        tactical_data = progression_data.get('tactical_improvement', {})
        if tactical_data:
            fig.add_trace(
                go.Bar(
                    x=['Error Rate', 'Missed Tactics'],
                    y=[
                        tactical_data.get('error_rate_improvement', 0),
                        tactical_data.get('tactical_vision_improvement', 0)
                    ],
                    marker_color=[self.color_scheme['success'], self.color_scheme['primary']],
                    name="Improvement"
                ),
                row=2, col=1
            )
        
        # Opening evolution
        opening_data = progression_data.get('opening_evolution', {})
        if opening_data:
            fig.add_trace(
                go.Bar(
                    x=['Early Repertoire', 'Current Repertoire'],
                    y=[
                        opening_data.get('early_diversity', 0),
                        opening_data.get('recent_diversity', 0)
                    ],
                    marker_color=[self.color_scheme['info'], self.color_scheme['primary']],
                    name="Repertoire Size"
                ),
                row=2, col=2
            )
        
        # Consistency radar
        consistency_data = progression_data.get('consistency_metrics', {})
        if consistency_data:
            fig.add_trace(go.Scatterpolar(
                r=[
                    consistency_data.get('score_consistency', 0),
                    consistency_data.get('accuracy_consistency', 0),
                    100 - (consistency_data.get('performance_volatility', 0) * 100)
                ],
                theta=['Score', 'Accuracy', 'Stability'],
                fill='toself',
                name='Consistency',
                line_color=self.color_scheme['primary']
            ), row=3, col=1)
        
        # Summary table
        summary_data = progression_data.get('summary', {})
        if summary_data:
            insights = summary_data.get('key_insights', [])
            areas_to_work = summary_data.get('areas_needing_work', [])
            
            table_data = []
            for insight in insights[:3]:  # Top 3 insights
                table_data.append(['✅ Strength', insight])
            for area in areas_to_work[:3]:  # Top 3 areas
                table_data.append(['⚠️ Improvement', area])
            
            if table_data:
                fig.add_trace(
                    go.Table(
                        header=dict(values=['Type', 'Description']),
                        cells=dict(values=list(zip(*table_data)) if table_data else [[], []])
                    ),
                    row=3, col=2
                )
        
        fig.update_layout(
            height=1000,
            title_text="Chess Progression Dashboard",
            showlegend=False
        )
        
        return fig
    
    def create_improvement_velocity_chart(self, progression_data: Dict) -> go.Figure:
        """Create improvement velocity visualization."""
        velocity_data = progression_data.get('improvement_velocity', {})
        if not velocity_data:
            return self._create_no_data_figure("No improvement velocity data available")
        
        metrics = list(velocity_data.keys())
        velocities = list(velocity_data.values())
        
        # Color code based on improvement direction
        colors = []
        for v in velocities:
            if v > 0:
                colors.append(self.color_scheme['success'])
            elif v < 0:
                colors.append(self.color_scheme['warning'])
            else:
                colors.append(self.color_scheme['info'])
        
        fig = go.Figure(data=[
            go.Bar(
                x=metrics,
                y=velocities,
                marker_color=colors,
                text=[f"{v:+.3f}" for v in velocities],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="Improvement Velocity (Rate of Change)",
            yaxis_title="Improvement Rate",
            xaxis_title="Metrics",
            height=400
        )
        
        return fig
    
    def _create_no_data_figure(self, message: str) -> go.Figure:
        """Create a placeholder figure when no data is available."""
        fig = go.Figure()
        
        fig.add_annotation(
            x=0.5, y=0.5,
            text=message,
            showarrow=False,
            font=dict(size=16),
            xref="paper", yref="paper"
        )
        
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=300
        )
        
        return fig
    
    def save_all_charts(self, progression_data: Dict, output_dir: str = "charts") -> Dict[str, str]:
        """
        Generate and save all progression charts.
        
        Args:
            progression_data: Results from ProgressionAnalyzer
            output_dir: Directory to save charts
            
        Returns:
            Dictionary mapping chart names to file paths
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        charts = {
            'rating_progression': self.create_rating_progression_chart(progression_data),
            'accuracy_trends': self.create_accuracy_trends_chart(progression_data),
            'tactical_improvement': self.create_tactical_improvement_chart(progression_data),
            'opening_evolution': self.create_opening_evolution_chart(progression_data),
            'consistency_metrics': self.create_consistency_metrics_chart(progression_data),
            'comprehensive_dashboard': self.create_comprehensive_dashboard(progression_data),
            'improvement_velocity': self.create_improvement_velocity_chart(progression_data)
        }
        
        saved_files = {}
        for chart_name, fig in charts.items():
            file_path = os.path.join(output_dir, f"{chart_name}.html")
            fig.write_html(file_path)
            saved_files[chart_name] = file_path
            logger.info(f"Saved {chart_name} chart to {file_path}")
        
        return saved_files


def main():
    """Example usage of the progression visualizer."""
    # This would typically be called with real progression data
    sample_data = {
        'rating_progression': {
            'current_rating': 1650,
            'starting_rating': 1500,
            'peak_rating': 1700,
            'total_gain': 150,
            'trend_direction': 'improving'
        },
        'accuracy_trends': {
            'current_accuracy': 78.5,
            'starting_accuracy': 72.1,
            'accuracy_improvement': 6.4
        },
        'tactical_improvement': {
            'error_rate_improvement': 1.2,
            'tactical_vision_improvement': 0.8
        }
    }
    
    visualizer = ProgressionVisualizer()
    
    # Create sample charts
    rating_chart = visualizer.create_rating_progression_chart(sample_data)
    accuracy_chart = visualizer.create_accuracy_trends_chart(sample_data)
    dashboard = visualizer.create_comprehensive_dashboard(sample_data)
    
    print("Sample progression visualizations created!")
    print("In a real implementation, these would be displayed in Jupyter notebooks or saved as HTML files.")


if __name__ == "__main__":
    main()