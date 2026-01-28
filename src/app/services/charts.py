import matplotlib.pyplot as plt
import io
import datetime

class ChartService:
    @staticmethod
    def create_growth_chart(measurements_weight, measurements_height):
        """
        Generates a chart with two subplots: Weight and Height.
        measurements: list of (date, value)
        """
        plt.style.use('bmh') # Clean style
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Weight
        if measurements_weight:
            dates = [m[0] for m in measurements_weight]
            values = [m[1]/1000 for m in measurements_weight] # Convert g to kg
            
            ax1.plot(dates, values, marker='o', color='#e74c3c', label='Peso (kg)')
            ax1.set_title("Crescita Peso")
            ax1.set_ylabel("Kg")
            ax1.grid(True)
            ax1.legend()
            
            # Annotate last
            last_date = dates[-1]
            last_val = values[-1]
            ax1.annotate(f"{last_val:.2f} kg", (last_date, last_val), textcoords="offset points", xytext=(0,10), ha='center')

        # Height
        if measurements_height:
            dates = [m[0] for m in measurements_height]
            values = [m[1] for m in measurements_height]
            
            ax2.plot(dates, values, marker='s', color='#3498db', label='Altezza (cm)')
            ax2.set_title("Crescita Altezza")
            ax2.set_ylabel("Cm")
            ax2.grid(True)
            ax2.legend()
            
            last_date = dates[-1]
            last_val = values[-1]
            ax2.annotate(f"{last_val} cm", (last_date, last_val), textcoords="offset points", xytext=(0,10), ha='center')

        fig.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)
        
        return buf
