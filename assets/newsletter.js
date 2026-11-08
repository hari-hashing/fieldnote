(() => {
  const form=document.getElementById('newsletter-form'); if(!form)return;
  const api=String(window.FIELDNOTE_NEWSLETTER_API||'').trim().replace(/\/$/,'');
  const email=document.getElementById('newsletter-email'), timezone=document.getElementById('newsletter-timezone'), hour=document.getElementById('newsletter-hour');
  const status=document.getElementById('newsletter-status'), button=form.querySelector('button[type="submit"]');
  const detected=(()=>{try{return Intl.DateTimeFormat().resolvedOptions().timeZone||'UTC'}catch(_){return 'UTC'}})(); timezone.value=detected;
  const set=(msg,kind='')=>{status.textContent=msg;status.dataset.kind=kind};
  form.addEventListener('submit',async e=>{
    e.preventDefault(); if(!api){set('Newsletter subscriptions are not active yet. The site administrator must deploy the email service and configure its API URL.','error');return}
    if(!form.reportValidity())return; button.disabled=true;button.textContent='Submitting…';set('Sending your confirmation email…');
    try{const response=await fetch(api+'/subscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:email.value.trim(),timezone:timezone.value.trim(),deliveryHour:Number(hour.value),consent:document.getElementById('newsletter-consent').checked,company:form.elements.company.value})});const body=await response.json().catch(()=>({}));if(!response.ok)throw new Error(body.error||'Subscription could not be created.');set(body.message||'Check your inbox to confirm your subscription.','success');form.reset();timezone.value=detected;hour.value='9'}catch(err){set(err.message||'Unable to subscribe right now.','error')}finally{button.disabled=false;button.innerHTML='Subscribe to the weekly digest <span>↗</span>'}
  });
})();
