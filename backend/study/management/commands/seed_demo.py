import hashlib, os
from io import BytesIO
from reportlab.pdfgen.canvas import Canvas
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils import timezone
from study.models import Space,Project,Material,Job
from study.learning import event,refresh_context
PAGES = [
('Photosynthesis: the big picture',[
'Photosynthesis converts light energy into chemical energy stored in glucose.',
'Plants absorb carbon dioxide from the air and water from the soil.',
'Using sunlight, plants produce glucose and release oxygen as a byproduct.',
'The overall equation is 6 CO2 + 6 H2O + light -> C6H12O6 + 6 O2.',
'Chloroplasts are the organelles where photosynthesis occurs.',
'Chlorophyll is a pigment that absorbs mostly red and blue light.',
'Green light is mostly reflected, giving leaves their green appearance.']),
('Light-dependent reactions',[
'Light-dependent reactions take place in the thylakoid membranes.',
'Chlorophyll absorbs photons, exciting electrons to higher energy levels.',
'Water is split to replace electrons, releasing oxygen and hydrogen ions.',
'An electron transport chain builds a proton gradient across the membrane.',
'ATP synthase uses this gradient to produce ATP from ADP and phosphate.',
'NADP+ accepts electrons to form NADPH. ATP and NADPH carry energy.',
'ATP and NADPH power the Calvin cycle. Oxygen is released into the air.']),
('The Calvin cycle and limiting factors',[
'The Calvin cycle occurs in the stroma of the chloroplast.',
'Rubisco fixes carbon dioxide by attaching it to RuBP.',
'ATP and NADPH are used to reduce the resulting molecules into G3P.',
'Some G3P leaves the cycle to form sugars; the rest regenerates RuBP.',
'The cycle does not directly require light, but uses light reaction products.',
'Light intensity, carbon dioxide concentration and temperature can limit rate.',
'Increasing one factor helps only until another factor becomes limiting.',
'Very high temperatures can reduce the rate by denaturing enzymes.'])]
def sample_pdf():
    out=BytesIO();c=Canvas(out,pagesize=(612,792),invariant=True)
    for title,lines in PAGES:
        c.setTitle('Photosynthesis - Seeded demo study material')
        c.setFillColorRGB(.15,.4,.32);c.setFont('Helvetica-Bold',22);c.drawString(40,735,title)
        c.setFillColorRGB(.2,.25,.3);c.setFont('Helvetica',11)
        for i,line in enumerate(lines):c.drawString(40,680-i*30,line)
        c.setFont('Helvetica',9);c.drawString(40,45,'STUDIA | Seeded demo material | Text-only learning reference');c.showPage()
    c.save();return out.getvalue()
class Command(BaseCommand):
    help='Seed labeled study material; queue real processing without synthetic learning results'
    def add_arguments(self,p):
        p.add_argument('--username',default='demo');p.add_argument('--admin',action='store_true')
    def handle(self,*args,**opts):
        password=os.getenv('DEMO_PASSWORD')
        if not password:raise CommandError('Set DEMO_PASSWORD. No default password is shipped.')
        u,created=get_user_model().objects.get_or_create(username=opts['username'])
        if created:u.set_password(password);u.is_staff=opts['admin'];u.save()
        s,_=Space.objects.get_or_create(owner=u,name='Natural sciences',defaults={'description':'Explore the living world, one concept at a time.'})
        p,_=Project.objects.get_or_create(space=s,name='The science of photosynthesis',defaults={'description':'From sunlight to sugar: understand how plants power life.','goal':'Explain light reactions and the Calvin cycle; predict how limiting factors affect photosynthesis.','is_demo':True})
        body=sample_pdf();digest=hashlib.sha256(body).hexdigest()
        if not Material.objects.filter(project=p,digest=digest).exists():
            m=Material(project=p,name='Photosynthesis - demo notes.pdf',digest=digest);m.file.save('photosynthesis.pdf',ContentFile(body));m.save()
            Job.objects.create(material=m,owner=u,available=timezone.now());event(p,'project_created',f'created:{p.id}',{'seeded_demo':True});event(p,'material_uploaded',f'upload:{m.id}',{'seeded_demo':True})
        refresh_context(p);self.stdout.write(f'Demo project {p.id} saved. Run worker for real AI processing.')
