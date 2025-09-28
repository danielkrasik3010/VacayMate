# Quick Start Guide
###  Run Defensive System:
```bash
cd VacayMate/UI
streamlit run defensive_app.py --server.port 8502
```
Then open: http://localhost:8502

###  Run Original System:
```bash
cd VacayMate/UI  
streamlit run app.py --server.port 8501
```
Then open: http://localhost:8501


##  What to Test:

1. **Normal Operation**: Amsterdam → Paris (future dates)
2. **Invalid Cities**: InvalidCity123 → FakeDestination456  
3. **Past Dates**: Any cities with dates from 2024
4. **System Health**: Check the "System Health Monitor" section
5. **Circuit Breakers**: Watch for API failure handling

##  Key Differences:

- **Original**: Basic functionality, may crash on errors
- **Defensive**: Enhanced with 6 defensive patterns, prevents most crashes
- **Health Monitoring**: Only in defensive system
- **Error Handling**: Graceful in defensive system

## Defensive Features to Notice:

- Real-time circuit breaker status
- Enhanced error messages  
- Past date warnings
- System statistics dashboard
- Fallback responses during API failures
- Green/gray defensive theme
